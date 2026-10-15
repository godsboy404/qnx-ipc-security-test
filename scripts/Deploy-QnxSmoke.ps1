param([Parameter(Mandatory=$true)][string]$TargetAddress)
$ErrorActionPreference = 'Stop'
if ($TargetAddress -notmatch '^\d{1,3}(\.\d{1,3}){3}$') { throw 'Expected registered VM IPv4 address' }
$projectRoot = Split-Path -Parent $PSScriptRoot
$key = Join-Path $projectRoot 'build/lab-keys/qnx-lab-ed25519'
$knownHosts = Join-Path $projectRoot 'build/qnx-vm/local/ssh-ident'
$ssh = "$env:WINDIR/System32/OpenSSH/ssh.exe"
$scp = "$env:WINDIR/System32/OpenSSH/scp.exe"
$sshOptions = @('-i',$key,'-o','BatchMode=yes','-o','IdentitiesOnly=yes',
    '-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o',"UserKnownHostsFile=$knownHosts",
    '-o','MACs=hmac-sha2-256','-o','Ciphers=aes128-ctr')
$target = "root@$TargetAddress"
function Invoke-SmokeWithDeadline {
    param([string]$OutputPath)
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $ssh
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    foreach ($arg in $sshOptions) { $info.ArgumentList.Add($arg) }
    $info.ArgumentList.Add($target)
    $info.ArgumentList.Add('route delete default >/dev/null 2>&1; cd /data/ipcsec-lab && chmod 700 hello-qnx lab-resmgr lab-client && sh run-smoke.sh')
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit(45000)) {
        $process.Kill()
        $process.WaitForExit()
        $stdout.Result | Set-Content -LiteralPath $OutputPath -Encoding utf8
        $stderr.Result | Set-Content -LiteralPath "$OutputPath.stderr" -Encoding utf8
        '{"host_watchdog":"TIMEOUT","target_fault":"UNKNOWN","isolation":"INCONCLUSIVE"}' |
            Set-Content -LiteralPath "$OutputPath.watchdog.json" -Encoding utf8
        throw '45-second host deadline reached; target status is UNKNOWN, not a confirmed crash'
    }
    $stdout.Result | Tee-Object -FilePath $OutputPath
    $stderr.Result | Set-Content -LiteralPath "$OutputPath.stderr" -Encoding utf8
    if ($process.ExitCode -ne 0) { throw "Remote smoke failed with exit code $($process.ExitCode)" }
}
Push-Location $projectRoot
try {
    & $ssh @sshOptions $target 'uname -a; mkdir -p /data/ipcsec-lab'
    if ($LASTEXITCODE -ne 0) { throw 'VM identity/session check failed' }
    foreach ($file in @('hello-qnx','lab-resmgr','lab-client')) {
        & $scp @sshOptions "build/native-x86_64/$file" "${target}:/data/ipcsec-lab/$file"
        if ($LASTEXITCODE -ne 0) { throw "Deployment failed: $file" }
    }
    & $scp @sshOptions 'native/qnx/run-smoke.sh' "${target}:/data/ipcsec-lab/run-smoke.sh"
    if ($LASTEXITCODE -ne 0) { throw 'Deployment failed: run-smoke.sh' }
    $runId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
    $dest = Join-Path $projectRoot "evidence/native-runs/$runId"
    New-Item -ItemType Directory -Path $dest | Out-Null
    & $ssh @sshOptions $target 'uname -a; id; ifconfig vmx0; netstat -rn' |
        Set-Content -LiteralPath "$dest/target-info.txt" -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'Target metadata collection failed' }
    # Keep the VM reachable on its development subnet but remove the guest's external route.
    Invoke-SmokeWithDeadline -OutputPath "$dest/smoke-output.txt"
    foreach ($file in @('hello.txt','normal.jsonl','empty.jsonl','restarted.jsonl','resmgr.log','resmgr-restart.log')) {
        & $scp @sshOptions "${target}:/data/ipcsec-lab/$file" "$dest/$file"
        if ($LASTEXITCODE -ne 0) { throw "Result collection failed: $file" }
    }
    $manifest = [ordered]@{ run_id=$runId; backend='qnx-native'; target_id='lab-resmgr-01';
        criterion_ids=@('IPC-01','REL-01'); evidence_source='local_host_ssh_runner';
        peer_reproduced=$false; human_signoff='pending'; isolation_verdict='INCONCLUSIVE';
        scope='legal ECHO, empty payload, owned server stop/start only';
        hashes=[ordered]@{}; source_hashes=[ordered]@{} }
    $manifest['host_deadline_seconds'] = 45
    $manifest['build'] = [ordered]@{ variant='gcc_ntox86_64'; flags='-std=c11 -D_QNX_SOURCE -Wall -Wextra -Werror'; binary_hashes=[ordered]@{} }
    foreach ($file in @('hello-qnx','lab-resmgr','lab-client')) {
        $manifest.build.binary_hashes[$file] = (Get-FileHash -LiteralPath "build/native-x86_64/$file" -Algorithm SHA256).Hash.ToLower()
    }
    foreach ($file in Get-ChildItem -LiteralPath $dest -File) {
        $manifest.hashes[$file.Name] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
    }
    foreach ($file in Get-ChildItem -LiteralPath 'native/qnx' -Recurse -File) {
        $name = [IO.Path]::GetRelativePath($projectRoot,$file.FullName).Replace('\','/')
        $manifest.source_hashes[$name] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
    }
    foreach ($file in @('scripts/Build-QnxNative.ps1','scripts/Deploy-QnxSmoke.ps1','scripts/Initialize-QnxEnvironment.ps1')) {
        $manifest.source_hashes[$file] = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLower()
    }
    $manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$dest/manifest.json" -Encoding utf8
    Write-Output "Native evidence: $dest"
} finally { Pop-Location }
