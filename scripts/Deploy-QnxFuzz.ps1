param(
    [Parameter(Mandatory=$true)][string]$TargetAddress,
    [ValidateRange(16,200)][int]$Count=128,
    [int]$Seed=20261015,
    [ValidateSet('baseline','defense')][string]$Mode='baseline',
    [ValidateSet('mixed','rate','authorization')][string]$Suite='mixed',
    [ValidateSet('allow','deny')][string]$Authorization='allow',
    [string]$PythonExecutable='python',
    [string]$ReplayRun='',
    [ValidatePattern('^[A-Z0-9_-]{1,31}$')][string]$ReplayCase='NF-0004'
)
$ErrorActionPreference='Stop'
if($TargetAddress -notmatch '^\d{1,3}(\.\d{1,3}){3}$'){throw 'Expected the registered VM IPv4 address'}
$root=Split-Path -Parent $PSScriptRoot
$key=Join-Path $root 'build/lab-keys/qnx-lab-ed25519'
$known=Join-Path $root 'build/qnx-vm/local/ssh-ident'
$ssh="$env:WINDIR/System32/OpenSSH/ssh.exe"
$scp="$env:WINDIR/System32/OpenSSH/scp.exe"
$opts=@('-i',$key,'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=10',
    '-o','StrictHostKeyChecking=yes','-o',"UserKnownHostsFile=$known",'-o','MACs=hmac-sha2-256','-o','Ciphers=aes128-ctr')
$target="root@$TargetAddress"
$runId=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)
$dest=Join-Path $root "evidence/native-fuzz-runs/$runId"
$remote="/data/ipcsec-lab/fuzz/$runId"
Push-Location $root
try {
    if($ReplayRun){
        $source=(Resolve-Path -LiteralPath $ReplayRun).Path
        $allowed=[IO.Path]::GetFullPath((Join-Path $root 'evidence/native-fuzz-runs'))+[IO.Path]::DirectorySeparatorChar
        if(-not $source.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Replay source must be a local project fuzz run'}
        & $PythonExecutable -m ipcsec.native replay $source $dest --case-id $ReplayCase
    }else{ & $PythonExecutable -m ipcsec.native prepare-policy $dest --count $Count --seed $Seed --mode $Mode --suite $Suite --authorization $Authorization }
    if($LASTEXITCODE -ne 0){throw 'Corpus preparation failed'}
    $corpusMeta=Get-Content "$dest/corpus-meta.json" -Raw | ConvertFrom-Json
    & $ssh @opts $target "test ! -e /dev/ipcsec-lab && mkdir -p $remote && uname -a"
    if($LASTEXITCODE -ne 0){throw 'VM/owned-target precondition failed; no execution'}
    foreach($file in @('lab-resmgr','lab-fuzzer','lab-monitor')){
        & $scp @opts "build/native-x86_64/$file" "${target}:$remote/$file"
        if($LASTEXITCODE -ne 0){throw "Deployment failed: $file"}
    }
    & $scp @opts "$dest/corpus.tsv" 'native/qnx/run-fuzz.sh' "${target}:$remote/"
    if($LASTEXITCODE -ne 0){throw 'Corpus/script deployment failed'}
    if($corpusMeta.schema_version -eq 2){
        & $scp @opts "$dest/defense-mode.txt" "$dest/authorization.txt" "${target}:$remote/"
        if($LASTEXITCODE -ne 0){throw 'Policy deployment failed'}
    }
    if($corpusMeta.authorization_control){
        & $scp @opts "$dest/authorization-plan.txt" "${target}:$remote/"
        if($LASTEXITCODE -ne 0){throw 'Authorization plan deployment failed'}
    }
    & $ssh @opts $target 'uname -a; id; netstat -rn' | Set-Content "$dest/target-info.txt" -Encoding utf8
    if($LASTEXITCODE -ne 0){throw 'Target metadata collection failed'}
    $info=[Diagnostics.ProcessStartInfo]::new()
    $info.FileName=$ssh;$info.UseShellExecute=$false;$info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
    foreach($arg in $opts){$info.ArgumentList.Add($arg)}
    $info.ArgumentList.Add($target)
    $info.ArgumentList.Add("route delete default >/dev/null 2>&1; cd $remote && sh run-fuzz.sh")
    $process=[Diagnostics.Process]::new();$process.StartInfo=$info;[void]$process.Start()
    $stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync()
    $timedOut=-not $process.WaitForExit(45000)
    if($timedOut){$process.Kill();$process.WaitForExit()}
    $stdout.Result | Set-Content "$dest/host-stdout.txt" -Encoding utf8
    $stderr.Result | Set-Content "$dest/host-stderr.txt" -Encoding utf8
    @{host_watchdog_timeout=$timedOut;remote_exit_code=$process.ExitCode;deadline_seconds=45} |
        ConvertTo-Json | Set-Content "$dest/host-execution.json" -Encoding utf8
    # Preserve available partial observations even when a worker failed.
    $evidenceFiles=@('fuzz-results.jsonl','fuzzer-meta.json','monitor.jsonl','monitor-summary.json',
                      'monitor-selftest.json','heartbeat.jsonl','cleanup.json','native-stdout.txt','native-stderr.txt')
    if($corpusMeta.schema_version -eq 2){$evidenceFiles+=@('target-audit.jsonl','policy-selftest.json')}
    if($corpusMeta.authorization_control){$evidenceFiles+='authorization-events.jsonl'}
    foreach($file in $evidenceFiles){
        & $scp @opts "${target}:$remote/$file" "$dest/$file"
        if($LASTEXITCODE -ne 0){Write-Warning "Evidence unavailable: $file"}
    }
    $manifest=[ordered]@{run_id=$runId;backend='qnx-native';target_id='lab-resmgr-01';device='/dev/ipcsec-lab';
        evidence_source='local_host_ssh_runner';peer_reproduced=$false;human_signoff='pending';
        source_hashes=[ordered]@{};binary_hashes=[ordered]@{};evidence_hashes=[ordered]@{};
        scope='bounded local devctl inputs, separate waitpid monitor and peer heartbeat';
        isolation_verdict='INCONCLUSIVE'}
    foreach($file in @('lab-resmgr','lab-fuzzer','lab-monitor')){
        $manifest.binary_hashes[$file]=(Get-FileHash "build/native-x86_64/$file" -Algorithm SHA256).Hash.ToLower()
    }
    foreach($dir in @('native/qnx','ipcsec')){
        foreach($file in Get-ChildItem -LiteralPath $dir -Recurse -File | Where-Object FullName -NotMatch '__pycache__'){
            $name=[IO.Path]::GetRelativePath($root,$file.FullName).Replace('\','/')
            $manifest.source_hashes[$name]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
        }
    }
    foreach($file in @('scripts/Deploy-QnxFuzz.ps1','scripts/Build-QnxNative.ps1','scripts/verify_native_fuzz_evidence.py','configs/native-lab.json','docs/specification.md')){
        $manifest.source_hashes[$file]=(Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
    }
    $analysisFailed=$true
    if(-not $timedOut){
        & $PythonExecutable -m ipcsec.native analyze $dest
        $analysisFailed=$LASTEXITCODE -ne 0
    }
    foreach($file in Get-ChildItem -LiteralPath $dest -File){
        $manifest.evidence_hashes[$file.Name]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
    }
    $manifest | ConvertTo-Json -Depth 6 | Set-Content "$dest/manifest.json" -Encoding utf8
    Write-Output "Native fuzz evidence: $dest"
    if($timedOut -or $process.ExitCode -ne 0 -or $analysisFailed){throw 'Run incomplete or evidence check failed; inspect preserved results, do not infer target crash'}
}finally{Pop-Location}
