# QNX虚拟机与合法IPC运行手册

本地环境为QNX SDP 8.0和VMware Workstation，目标架构x86_64。
以下操作只适用于本项目生成的新虚拟机，不连接或测试第三方目标。

## 初次建立

在项目根目录的PowerShell 7中运行：

```powershell
./scripts/Build-QnxVm.ps1
./scripts/Build-QnxNative.ps1
./scripts/Start-QnxVm.ps1 -NetworkMode nat
```

生成的VM配置位于build/qnx-vm/local/vmware_files/vmware.vmx，磁盘、运行状态和SSH密钥均在build内。
VMware中可使用File Open打开该vmx。镜像构建依赖官方工具的Bash，受限沙箱可能需要系统批准。
不要在运行中的虚拟机上直接重新构建镜像，不要使用wipe或clean代替常规重置。

本机Host-only的VMnet1未分配IP，因此实际使用已启用的VMnet8开发连接，未修改Windows网卡配置。
部署脚本移除Guest默认路由，仅保留开发网段；该设置不代表完整网络隔离。其他主机环境应优先确认Host-only可用性。

## 确定目标地址

从VMware的DHCP租约中按本VM的MAC地址匹配地址，不能猜IP后连接。
SSH使用镜像生成时预置的主机公钥进行严格校验，身份和known-host文件均位于build内。
本机Windows OpenSSH与QNX默认协商出现过MAC兼容错误，脚本明确使用AES128-CTR及HMAC-SHA256。

## 部署和验证

```powershell
./scripts/Deploy-QnxSmoke.ps1 -TargetAddress <已确认的VM地址>
python scripts/verify_native_evidence.py
```

脚本部署Hello、lab-resmgr、lab-client和固定Smoke流程到/data/ipcsec-lab。
Smoke执行100次ping、1次空载荷，停止自己启动的服务，检查路径解绑，重启后再执行100次ping。
每条请求记录实际载荷与devctl字节数、错误码和真实耗时。该合法基线不报告崩溃或隔离成功率。
客户端配置SEND/REPLY截止2秒，远程Smoke主机截止45秒；专用gate检查点下的发送侧超时另见native-recovery-runbook.md，不代表所有回复侧阻塞都可直接解除。
运行结束会清理本次服务，防止留下未知后台进程。若设备路径预先存在，则拒绝接管该服务。

## 恢复

基线快照为IPC-Ready-20261015。回滚会丢弃Guest在快照之后的更改，先将所需结果取回主机。
Test-QnxSnapshot.ps1只用于无待保存工作的新实验机，它会创建临时标记、回滚、显式启动并验证标记消失和Hello运行。
VMware的revertToSnapshot调用可能把VM留在关机状态，必须启动后等待网络恢复。
SSH若返回Not allowed at this time，保留原文，稍后重试；不关闭SSH防护、不自动绕过主机密钥检查。
恢复验证的最新结果见review/native-milestone.md。

## 当前范围

原生Fuzzer、客户端网关、限流、动态授权、独立监督、只读OS探针及限定恢复已有实测。完整系统隔离、评价器模型环节和伙伴独立复现仍未完成。
教师选题接受状态及个人签署仍待填写；用户后续已授权同一自建VM的有界变异、防御和受控恢复，不覆盖系统服务攻击或第三方目标。
