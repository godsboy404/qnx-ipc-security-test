param([Parameter(Mandatory=$true)][string]$TargetAddress, [switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
if ($TargetAddress -notmatch '^\d{1,3}(\.\d{1,3}){3}$') { throw 'Expected registered VM IPv4 address' }
$projectRoot = Split-Path -Parent $PSScriptRoot
$vmx = Join-Path $projectRoot 'build/qnx-vm/local/vmware_files/vmware.vmx'
$key = Join-Path $projectRoot 'build/lab-keys/qnx-lab-ed25519'
$known = Join-Path $projectRoot 'build/qnx-vm/local/ssh-ident'
$ssh = "$env:WINDIR/System32/OpenSSH/ssh.exe"
$opts = @('-i',$key,'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=5',
    '-o','StrictHostKeyChecking=yes','-o',"UserKnownHostsFile=$known",'-o','MACs=hmac-sha2-256','-o','Ciphers=aes128-ctr')
$target = "root@$TargetAddress"
if (-not $VerifyOnly) {
    & $ssh @opts $target 'test ! -e /dev/ipcsec-lab && test -d /data/ipcsec-lab && echo snapshot-probe > /data/ipcsec-lab/post-snapshot-marker && test -f /data/ipcsec-lab/post-snapshot-marker'
    if ($LASTEXITCODE -ne 0) { throw 'Restore precondition failed; no rollback performed' }
    & 'C:/Program Files/VMware/VMware Workstation/vmrun.exe' -T ws revertToSnapshot $vmx 'IPC-Ready-20261015'
    if ($LASTEXITCODE -ne 0) { throw 'Snapshot restore failed' }
}
# vmrun revert restores the saved state but may leave the VM powered off.
& "$PSScriptRoot/Start-QnxVm.ps1" -NetworkMode nat
for ($attempt=1; $attempt -le 6; $attempt++) {
    & $ssh @opts $target 'test ! -e /data/ipcsec-lab/post-snapshot-marker && /data/ipcsec-lab/hello-qnx && echo SNAPSHOT_RESTORE_OK'
    if ($LASTEXITCODE -eq 0) { return }
    if ($attempt -lt 6) { Start-Sleep -Seconds 2 }
}
throw 'Snapshot restored but marker or Hello verification failed after bounded reconnect'
