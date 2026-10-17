# 课堂演示顺序与结论口径

建议按“问题—对照—观测—失败修复—限制”组织。先使用已保存证据核验，再按时间和环境决定是否现场执行，避免将VM启动或网络等待占满讲述。

## 1. 说明目标与范围

展示自建/dev/ipcsec-lab、64字节应用载荷上限、实际长度与声明长度分开校验。说明运行环境为项目自建QNX 8.0 VM，测试没有扫描系统服务或第三方目标。教师批准状态和个人贡献签署按实际填写。

## 2. 展示攻防对照

打开review/native-defense-milestone.md及对应comparison.json。相同128例，baseline转发128次；开启客户端网关后94非法输入BLOCK、14合法请求RATE_LIMIT、20次应答。强调目标端独立审计与forwarded记录一致，不能只展示客户端“拦截成功”的文字。
再展示24例专用限流：同会话超额请求拒绝，另一会话通过，等待窗口过期后恢复。窗口端点精确校准与真实时钟实验分别说明。

## 3. 展示动态授权

打开review/native-authorization-milestone.md。两轮各24例，允许、撤销、缺文件、坏格式、目标不符和恢复依次发生；8次应答、16次SCOPE_DENY。展示独立监督进程的authorization-events.jsonl与服务端8条接收记录。

## 4. 展示真实超时与恢复

在项目根目录执行只读验证：

```powershell
python -m ipcsec.stall verify evidence/native-stall-runs/20261017T130224Z-8ed73897
python -m ipcsec.recovery verify evidence/native-recovery-runs/20261017T130304Z-d6c6072a
```

暂停模式中指出三个事实：waitpid确认目标停止、客户端约2.002秒返回ETIMEDOUT=260、SIGCONT后同PID正常应答。服务端21条记录只覆盖10 ping + 1 gate + 10 ping，没有超时请求的额外延迟交付。暂停期间设备可见性null表示没有查询，不能读成设备消失。
退出模式中则是SIGTERM终止、设备不可用、不同PID重启，不能和暂停模式混讲。

## 5. 展示失败与修复

展示review/native-stall-issue.md保留的4轮失败：暂停时查询目标导致监控阻塞，后来6秒兜底触发仍必须判FAIL，最后将检查点限定为专用gate ECHO才完成验收。解释2秒IPC截止、6秒异常恢复兜底、15秒监督预算和45秒宿主截止各自作用。不要把兜底恢复讲成2秒超时通过。

## 6. 收束结论与交付

当前实现能完成单目标真实IPC、有界变异、客户端防御与限流、动态授权、独立只读探针和限定恢复实验。网关可被直接设备访问绕过；实验会话不是可信身份；探针不是全系统健康证明；完整隔离为INCONCLUSIVE。伙伴独立复现及人工签署按实际补齐。
入口索引为review/evidence-index.md。若现场重跑，用native-fuzz-runbook.md和native-recovery-runbook.md，核对登记VM地址并为每次运行建立新目录；不要改写演示用历史证据。
