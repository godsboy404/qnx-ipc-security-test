# 受控服务停止与恢复运行手册

前提：项目自建QNX VM已启动，IP已按登记MAC核对，专用SSH密钥及固定主机密钥可用。PowerShell 7、QNX SDP 8和Python 3.10+；在项目根目录执行。

```powershell
./scripts/Build-QnxNative.ps1
./scripts/Deploy-QnxRecovery.ps1 -TargetAddress <登记VM的IPv4>
python -m ipcsec.recovery verify <本次生成的运行目录>
```

Python不在PATH时使用-PythonExecutable传入绝对路径。实测记录可只读复核：

```powershell
python -m ipcsec.recovery verify evidence/native-recovery-runs/20261017T124025Z-59242bdb
```

每次创建唯一evidence/native-recovery-runs/目录，部署到对应/data/ipcsec-lab/recovery/目录。已有/dev/ipcsec-lab时拒绝运行，不接管现存服务。
监督进程依次启动独立只读OS探针、自建服务及10次合法请求客户端；对自己创建的服务PID发SIGTERM，waitpid确认后检查设备解绑，用独立客户端确认open返回ENOENT。保留约200ms停机观测，再启动新PID服务并发送10次合法请求。探针执行uname和只读stat(/proc)，不变异系统服务消息。
最多20次合法IPC和1次停机open检查；IPC 2秒、监督15秒、宿主45秒。只回收本轮创建的子进程，未知进程不处理。连接中断先检查保留证据及自己创建的进程；必要时按qnx-vm-runbook.md恢复既有快照。

verify检查manifest哈希，重新核验退出信号、阶段顺序、独立PID、前后应答与接收字节、停机ENOENT、探针阶段覆盖和清理结果，不改写历史summary。失败或缺失不能解释为目标crash。
恢复时间有两种起点：停止请求与重启请求；两者都以首个正确应答结束。前者包含主动停机观察窗口，不用于冒充启动性能。单次观测不计算P95。
本实验为受控SIGTERM退出与恢复，完整隔离仍为INCONCLUSIVE。结果及后续任务见review/native-recovery-milestone.md。

## 暂停超时实验的当前状态

专用gate检查点版本已在用户重新要求继续后通过真实QNX验收，旧失败仍保留于review/native-stall-issue.md。最新结果见review/native-stall-milestone.md。

```powershell
./scripts/Deploy-QnxRecovery.ps1 -TargetAddress <登记VM的IPv4> -Scenario stall
python -m ipcsec.stall verify <本次生成的运行目录>
python -m ipcsec.stall verify evidence/native-stall-runs/20261017T130224Z-8ed73897
```

客户端先连接并发送专用合法gate ECHO；服务仅在显式--controlled-pause模式下，于该次回复完成后、下一次接收前暂停。监督确认SIGSTOP后才允许一次2秒截止的ping，确认ETIMEDOUT后SIGCONT恢复同一PID，再执行10次正常请求。总22次IPC尝试：前后各10次ping、1次gate、1次超时；服务端应只有21条接收记录。
6秒SIGALRM为异常恢复兜底，触发即FAIL，不能代替2秒IPC超时。暂停期间不查询目标设备，可见性以null记录。默认Scenario=stop仍为停止/新PID重启切片，最新共享代码已通过20261017T130304Z-d6c6072a原生回归。
该场景只验证发送侧超时，未覆盖服务器已接收消息后的全部回复侧解除阻塞语义，不宣称系统级隔离。
