# 伙伴独立复现步骤

状态：交接说明已备；伙伴尚未执行和签署。复现者应为课程规定的独立结对组，不用同一开发会话或AI自检代替。

## A. 核对交接包与来源

1. 记录收到的ZIP SHA256、发送人、接收时间和复现者。用SHA256SUMS.txt核对ZIP哈希，再解压到新的工作目录；哈希提供一致性检查，不证明发送人身份。
2. 在解压后的qnx-ipc-security-test根目录执行：

```powershell
python -m ipcsec.handoff audit
python -m unittest discover -s tests -v
```

审计报告中selected_evidence_status=PASS仅表示所选历史技术证据核验通过。course_gate=PENDING和peer_reproduced=false必须保留，直到实际人工记录支持更新。nonpassing_history应包含已保留的失败/未完成轮次。
SOURCE-SNAPSHOT.json标识包内当前源码。历史manifest各有自己的版本；historical_code_matches_current只比较该manifest列出的代码文件，不表示当前快照与旧构建完全相同。旧源码或二进制未完整保存时，不能从哈希恢复它们，也不能声称重建了旧版本。

## B. 独立主机验证

作者侧统一自检入口为 `python -m ipcsec.local_check run`，详见final-execution-guide.md。伙伴可以在自己的已核查副本运行同一工具，但输出仍保守标为host self-check，必须另附本人复现记录才能支持独立性。

```powershell
python -m ipcsec demo
python -m ipcsec calibrate
python -m ipcsec replay --case-id CASE-0001
```

这些是主机模拟，不是QNX证据。记录新run_id、命令、退出码、Python版本和不符合预期的结果。不要覆盖包内历史运行。按review/partner-reproduction-record.md填写，但不提前标PASS。

## C. 独立建立QNX环境

需要复现者自行合法安装QNX SDP 8、VMware Workstation、PowerShell 7和Windows OpenSSH。交接包不含SDK、VM磁盘、原构建二进制或SSH私钥。按qnx-vm-runbook.md创建自己的实验VM及专用身份，不能复制发送人的密钥或猜测沿用其IP。

```powershell
./scripts/Build-QnxNative.ps1
./scripts/Build-QnxVm.ps1
./scripts/Start-QnxVm.ps1 -NetworkMode nat
./scripts/Deploy-QnxSmoke.ps1 -TargetAddress <按本VM_MAC登记核对的IPv4>
```

若SDP不在默认位置，Build脚本使用-SdpRoot；Python不在PATH时，Fuzz/Recovery脚本使用-PythonExecutable。VMware路径或网络与当前脚本默认不同，先记录差异并调整自己的环境，不关闭SSH主机密钥核验。只有创建自己的新VM才运行Build-QnxVm，不对已有工作VM反复建镜像。
先完成自己的恢复快照并实际验证。现有Test-QnxSnapshot.ps1使用快照名IPC-Ready-20261015，该名称是原实验约定；伙伴必须在自己的VM上准备匹配快照或明确修改并记录脚本。回滚会丢弃Guest后续变化，先把结果取回主机。不得把包内原作者的快照恢复记录当作伙伴恢复验证。

## D. 用当前快照生成新的原生证据

每个命令会生成新目录。成对实验之间不改源码、配置、二进制或种子；先记录两次生成的目录，再交给compare。

```powershell
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <本VM_IP> -Mode baseline -Count 128
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <本VM_IP> -Mode defense -Count 128
python scripts/compare_native_defense.py <新baseline目录> <新defense目录>

./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <本VM_IP> -Mode baseline -Suite rate
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <本VM_IP> -Mode defense -Suite rate
python scripts/compare_native_defense.py <新rate_baseline目录> <新rate_defense目录>

./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <本VM_IP> -Mode defense -Suite authorization
./scripts/Deploy-QnxRecovery.ps1 -TargetAddress <本VM_IP> -Scenario stop
./scripts/Deploy-QnxRecovery.ps1 -TargetAddress <本VM_IP> -Scenario stall
```

混合语料的合法限流数量依真实时间而变，不要求机械复制原作者的14次限流；必须符合实时滑动窗口oracle、请求字段和服务端接收审计。非法94例均不得转发。rate专用24例应有2次限流；authorization应8次应答、16次拒绝。stall应真实返回ETIMEDOUT、同PID恢复、21条目标接收；6秒兜底触发为FAIL。
对新运行分别用verify_native_fuzz_evidence.py、ipcsec.recovery verify、ipcsec.stall verify核验。不要修改handoff-evidence.json来覆盖作者历史索引；伙伴的新运行另填记录并明确版本。

## E. 交接与结论

记录启动、重放、重置、恢复及一个失败/未知；分别提出可核查Claim、反例或缺证据项。若无法建立QNX环境，可完成A/B但原生复现记NOT_RUN，不能用历史包或simulation补成PASS。连续三次同类关键失败保存证据并登记问题。
最终人工签署限实际检查范围；完整系统隔离仍为INCONCLUSIVE。E2 Change需教师批准，E3独立审查、评价器模型校准及个人贡献另按课程流程完成。
