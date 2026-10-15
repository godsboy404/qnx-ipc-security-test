param([string]$SdpRoot = (Join-Path $env:USERPROFILE 'qnx800'))
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Initialize-QnxEnvironment.ps1" -SdpRoot $SdpRoot
$projectRoot = Split-Path -Parent $PSScriptRoot
$imageDir = Join-Path $projectRoot 'build/qnx-vm'
$keyDir = Join-Path $projectRoot 'build/lab-keys'
New-Item -ItemType Directory -Path $imageDir,$keyDir -Force | Out-Null
$keyFile = Join-Path $keyDir 'qnx-lab-ed25519'
if (-not (Test-Path -LiteralPath $keyFile)) {
    & "$env:WINDIR/System32/OpenSSH/ssh-keygen.exe" -q -t ed25519 -N '' -C 'qnx-ipc-local-lab' -f $keyFile
    if ($LASTEXITCODE -ne 0) { throw 'Lab SSH identity generation failed' }
}
$publicKey = "$keyFile.pub".Replace('\','/')
Push-Location $imageDir
try {
    # Preserve the official security defaults. Only this new image is built.
    & "$env:QNX_HOST/usr/bin/bash.exe" "$env:QNX_BASE/host/common/bin/mkqnximage" `
        --type=vmware --arch=x86_64 --hostname=qnx-ipc-lab --graphics=no `
        "--ssh-ident=$publicKey" --sshd-pregen=yes --users=root:qnxuser --cpu=2 --ram=1G --build
    if ($LASTEXITCODE -ne 0) { throw "mkqnximage failed: $LASTEXITCODE" }
} finally { Pop-Location }
