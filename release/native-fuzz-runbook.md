# 原生有界变异运行与重放

要求PowerShell 7、Python 3.10+、QNX SDP 8、本项目已创建的VM、专用SSH密钥和固定主机密钥。VM地址必须从其登记MAC及DHCP记录核对。所有命令在项目根目录运行。

```powershell
./scripts/Build-QnxNative.ps1
./scripts/Start-QnxVm.ps1 -NetworkMode nat
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -Count 128
python scripts/verify_native_fuzz_evidence.py <本次生成的运行目录>
```

若python不在PATH或使用其他环境，以-PythonExecutable传入可执行文件绝对路径。Count允许16至200，默认种子20261015。只部署到自建/data/ipcsec-lab/fuzz/唯一运行目录；已有/dev/ipcsec-lab时拒绝运行，不接管现存服务。

```powershell
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -ReplayRun evidence/native-fuzz-runs/20261017T121606Z-e29291df -ReplayCase NF-0004
python scripts/verify_native_fuzz_evidence.py <本次生成的运行目录>
```

重放校验源语料哈希及JSON/TSV一致性，保留用例原字段，另建运行目录。每次运行保存manifest及summary，不覆盖历史。只读verify脚本检查证据哈希并重新判定，不改写历史summary。manifest的哈希用于一致性核验，不是签名或独立第三方背书。

四个独立进程为monitor、target、worker、peer。实际载荷最多65字节，每次IPC 2秒、监督15秒、主机45秒。错误、缺记录或超时均不能推断crash。系统探针未实现，隔离结论保持INCONCLUSIVE。
运行结束只回收自己创建的进程；cleanup.json必须显示三个子进程均回收、设备不存在。如主机连接中断，先核对保留证据及自己启动的进程，勿按进程名称批量kill。必要时参考qnx-vm-runbook.md恢复IPC-Ready-20261015快照；恢复后需重新启动VM。

当前使用VMnet8并删除Guest默认路由，开发网段仍可达，不构成完整网络隔离。SSH主机密钥固定校验；不得为解决连接问题关闭认证。

## 防御开关、限流和授权对照

```powershell
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -Mode baseline -Count 128
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -Mode defense -Count 128
python scripts/compare_native_defense.py <baseline运行目录> <defense运行目录>

./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -Mode baseline -Suite rate
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -Mode defense -Suite rate
python scripts/compare_native_defense.py <rate的baseline目录> <rate的defense目录>

./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -Mode baseline -Authorization deny -Count 16
```

Mode默认baseline；baseline只关闭输入防御与限流，schema_version=2仍逐请求检查授权。Suite默认mixed；rate固定24例，忽略Count，两个会话分别突发，间隔一次1100ms等待。成对运行之间不修改源码、配置或二进制，否则compare会拒绝版本不同的对照。
defense-mode.txt、authorization.txt以固定ASCII格式部署；网关检查协议字段和实际长度，再限制每会话1秒最多10个合法请求尝试。网关位于客户端，不是不可绕过的系统拦截器。
target-audit.jsonl是服务端独立接收记录。analyze必须核对接收次数、字节、顺序、时间和PID；NOT_SENT不应有对应接收。policy-selftest.json使用合成时钟校准精确端点，真实突发及窗口恢复以rate运行证据为准。
重放继承源模式和授权配置；会话历史在新进程中重新开始，不能期待原来的RATE_LIMIT决定在单例重放中重现。旧schema_version=1重放保留旧的直接发送路径，仅用于有界历史实验。
最新事实和保留的失败轮次见review/native-defense-milestone.md。不带目录参数的verify会检查全历史，遇到保留的失败轮次返回非零；不能删除该轮次来使全历史显示通过。

## 动态授权与缺失文件验证

```powershell
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -Mode baseline -Suite authorization
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -Mode defense -Suite authorization
python scripts/compare_native_defense.py <authorization的baseline目录> <authorization的defense目录>
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记VM的IPv4> -ReplayRun evidence/native-fuzz-runs/20261017T123421Z-e4e1c71d -ReplayCase NA-0008
```

authorization固定24例，要求初始Authorization=allow，忽略Count。授权计划每4例依次为allow、deny、missing、malformed、wrong-target、allow。监督进程只修改本轮目录内authorization.txt；原子替换/移除并读回后，记录authorization-events.jsonl，再确认客户端读取。客户端确认等待最多2秒，确认失败不执行下一次IPC。
本地authorization.txt保留初始部署配置，远端动态状态依据独立事件的实际读回字节核验；不能将本地初始文件当作整个运行期间的授权状态。
预期两种模式均8次转发、16次SCOPE_DENY。服务端记录必须仅8条，最后4例恢复正常应答。重放只恢复所选用例的授权状态；NA-0008在新运行中实际删除私有授权文件，预期零转发。只保证变更确认后的下一请求重新检查，不取消已在途IPC，也不宣称配置文件防篡改。
