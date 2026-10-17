param([string]$SdpRoot = (Join-Path $env:USERPROFILE 'qnx800'))
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Initialize-QnxEnvironment.ps1" -SdpRoot $SdpRoot
$projectRoot = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $projectRoot 'build/native-x86_64'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
Push-Location $projectRoot
try {
    foreach ($item in @(@('hello-qnx','native/qnx/client/hello_qnx.c'),
                         @('lab-resmgr','native/qnx/target/lab_resmgr.c'),
                         @('lab-client','native/qnx/client/lab_client.c'),
                         @('lab-fuzzer','native/qnx/client/lab_fuzzer.c'),
                         @('lab-monitor','native/qnx/probes/lab_monitor.c'),
                         @('lab-recovery','native/qnx/probes/lab_recovery.c'))) {
        & "$env:QNX_HOST/usr/bin/qcc.exe" -Vgcc_ntox86_64 -std=c11 -D_QNX_SOURCE -Wall -Wextra -Werror `
            -Inative/qnx/include -o "$outDir/$($item[0])" $item[1]
        if ($LASTEXITCODE -ne 0) { throw "Native build failed: $($item[0])" }
        Write-Output "Built $($item[0])"
    }
} finally { Pop-Location }
