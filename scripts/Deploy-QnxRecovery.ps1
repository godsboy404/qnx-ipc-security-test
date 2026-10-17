param(
    [Parameter(Mandatory=$true)][string]$TargetAddress,
    [ValidateSet('stop','stall')][string]$Scenario='stop',
    [string]$PythonExecutable='python'
)
$ErrorActionPreference='Stop'
if($TargetAddress -notmatch '^\d{1,3}(\.\d{1,3}){3}$'){throw 'Expected the registered VM IPv4 address'}
$root=Split-Path -Parent $PSScriptRoot
$key=Join-Path $root 'build/lab-keys/qnx-lab-ed25519'
$known=Join-Path $root 'build/qnx-vm/local/ssh-ident'
$ssh="$env:WINDIR/System32/OpenSSH/ssh.exe";$scp="$env:WINDIR/System32/OpenSSH/scp.exe"
$opts=@('-i',$key,'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=10',
    '-o','StrictHostKeyChecking=yes','-o',"UserKnownHostsFile=$known",'-o','MACs=hmac-sha2-256','-o','Ciphers=aes128-ctr')
$target="root@$TargetAddress"
$runId=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)
$module=if($Scenario -eq 'stall'){'ipcsec.stall'}else{'ipcsec.recovery'}
$evidenceRoot=if($Scenario -eq 'stall'){'native-stall-runs'}else{'native-recovery-runs'}
$faultKind=if($Scenario -eq 'stall'){'controlled_SIGSTOP'}else{'controlled_SIGTERM'}
$dest=Join-Path $root "evidence/$evidenceRoot/$runId"
$remote="/data/ipcsec-lab/recovery/$runId"
Push-Location $root
try {
    & $PythonExecutable -m $module prepare $dest
    if($LASTEXITCODE -ne 0){throw 'Recovery preparation failed'}
    & $ssh @opts $target "test ! -e /dev/ipcsec-lab && mkdir -p $remote && uname -a"
    if($LASTEXITCODE -ne 0){throw 'Owned device precondition failed; no takeover'}
    & $scp @opts 'build/native-x86_64/lab-resmgr' 'build/native-x86_64/lab-recovery' 'native/qnx/run-recovery.sh' "${target}:$remote/"
    if($LASTEXITCODE -ne 0){throw 'Recovery deployment failed'}
    & $ssh @opts $target 'uname -a; id; netstat -rn' | Set-Content "$dest/target-info.txt" -Encoding utf8
    if($LASTEXITCODE -ne 0){throw 'Metadata collection failed'}
    $info=[Diagnostics.ProcessStartInfo]::new();$info.FileName=$ssh
    $info.UseShellExecute=$false;$info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
    foreach($arg in $opts){$info.ArgumentList.Add($arg)}
    $info.ArgumentList.Add($target)
    $info.ArgumentList.Add("route delete default >/dev/null 2>&1; cd $remote && sh run-recovery.sh $Scenario")
    $process=[Diagnostics.Process]::new();$process.StartInfo=$info;[void]$process.Start()
    $stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync()
    $timedOut=-not $process.WaitForExit(45000)
    if($timedOut){$process.Kill();$process.WaitForExit()}
    $stdout.Result | Set-Content "$dest/host-stdout.txt" -Encoding utf8
    $stderr.Result | Set-Content "$dest/host-stderr.txt" -Encoding utf8
    @{host_watchdog_timeout=$timedOut;remote_exit_code=$process.ExitCode;deadline_seconds=45} |
        ConvertTo-Json | Set-Content "$dest/host-execution.json" -Encoding utf8
    $files=if($Scenario -eq 'stall'){@('before.jsonl','after.jsonl','target-audit.jsonl','os-probe.jsonl',
        'stall-events.jsonl','stall-monitor.jsonl','stall-meta.json','stall-cleanup.json','stall-ready.json',
        'stall-request.json','stall-client-trace.jsonl','native-stdout.txt','native-stderr.txt')}else{@('before.jsonl','down.jsonl','after.jsonl','target-before.jsonl','target-after.jsonl',
        'os-probe.jsonl','recovery-events.jsonl','recovery-monitor.jsonl','recovery-meta.json',
        'recovery-cleanup.json','native-stdout.txt','native-stderr.txt')}
    foreach($file in $files){
        & $scp @opts "${target}:$remote/$file" "$dest/$file"
        if($LASTEXITCODE -ne 0){Write-Warning "Partial evidence unavailable: $file"}
    }
    $manifest=[ordered]@{run_id=$runId;backend='qnx-native';target_id='lab-resmgr-01';
        fault_kind=$faultKind;evidence_source='local_host_ssh_runner';peer_reproduced=$false;
        human_signoff='pending';isolation_verdict='INCONCLUSIVE';source_hashes=[ordered]@{};
        binary_hashes=[ordered]@{};evidence_hashes=[ordered]@{}}
    foreach($file in @('lab-resmgr','lab-recovery')){
        $manifest.binary_hashes[$file]=(Get-FileHash "build/native-x86_64/$file" -Algorithm SHA256).Hash.ToLower()
    }
    foreach($dir in @('native/qnx','ipcsec')){
        foreach($file in Get-ChildItem -LiteralPath $dir -Recurse -File | Where-Object FullName -NotMatch '__pycache__'){
            $name=[IO.Path]::GetRelativePath($root,$file.FullName).Replace('\','/')
            $manifest.source_hashes[$name]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
        }
    }
    foreach($file in @('scripts/Deploy-QnxRecovery.ps1','scripts/Build-QnxNative.ps1','docs/specification.md')){
        $manifest.source_hashes[$file]=(Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
    }
    $analysisFailed=$true
    if(-not $timedOut){
        & $PythonExecutable -m $module analyze $dest
        $analysisFailed=$LASTEXITCODE -ne 0
    }
    foreach($file in Get-ChildItem -LiteralPath $dest -File){
        $manifest.evidence_hashes[$file.Name]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
    }
    $manifest | ConvertTo-Json -Depth 6 | Set-Content "$dest/manifest.json" -Encoding utf8
    Write-Output "Recovery evidence: $dest"
    if($timedOut -or $process.ExitCode -ne 0 -or $analysisFailed){throw 'Recovery incomplete; evidence preserved, no crash inference'}
}finally{Pop-Location}
