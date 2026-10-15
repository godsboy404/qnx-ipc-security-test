param([string]$Vmrun = 'C:/Program Files/VMware/VMware Workstation/vmrun.exe',
      [ValidateSet('hostonly','nat')][string]$NetworkMode = 'hostonly')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$vmx = Join-Path $projectRoot 'build/qnx-vm/local/vmware_files/vmware.vmx'
if (-not (Test-Path -LiteralPath $vmx)) { throw 'Build the QNX image first' }
$running = & $Vmrun -T ws list
if ($LASTEXITCODE -ne 0) { throw 'Unable to list running VMware machines' }
if ($running -contains $vmx.Replace('/','\')) { Write-Output 'QNX VM already running'; exit 0 }
$text = Get-Content -LiteralPath $vmx -Raw
$text = $text -replace 'ethernet0.connectionType = "[^"]+"',"ethernet0.connectionType = `"$NetworkMode`""
$text = $text -replace 'vhv.enable = "TRUE"','vhv.enable = "FALSE"'
if ($text -notmatch 'serial0.present') {
    $text += "`nserial0.present = `"TRUE`"`nserial0.fileType = `"file`"`nserial0.fileName = `"../../output/console.log`"`n"
}
Set-Content -LiteralPath $vmx -Value $text -Encoding utf8
& $Vmrun -T ws start $vmx nogui
if ($LASTEXITCODE -ne 0) { throw 'VMware failed to start QNX VM' }
Write-Output "VM started: $vmx"
