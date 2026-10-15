param([string]$SdpRoot = (Join-Path $env:USERPROFILE 'qnx800'))
$ErrorActionPreference = 'Stop'
$resolvedSdp = (Resolve-Path -LiteralPath $SdpRoot).Path.Replace('\','/')
$env:QNX_BASE = $resolvedSdp
$env:QNX_HOST = "$resolvedSdp/host/win64/x86_64"
$env:QNX_TARGET = "$resolvedSdp/target/qnx"
$env:QNX_CONFIGURATION = (Join-Path $env:USERPROFILE '.qnx').Replace('\','/')
$env:QNX_CONFIGURATION_EXCLUSIVE = $env:QNX_CONFIGURATION
$env:MAKEFLAGS = "-I$env:QNX_TARGET/usr/include"
$env:PATH = "$env:QNX_HOST/usr/bin;$resolvedSdp/host/common/bin;$env:PATH"
$env:PYTHONDONTWRITEBYTECODE = '1'
if (-not (Test-Path -LiteralPath "$env:QNX_HOST/usr/bin/qcc.exe")) {
    throw 'qcc.exe not found in selected QNX SDP'
}
