# QNX IPC 安全测试课程项目

课程版：单个自建教学资源管理器的 IPC 对抗性测试与防御验证。

当前完成项目工程资产、主机模拟链路，以及QNX 8.0 x86_64虚拟机上的真实devctl ECHO链路。
Hello、100次合法请求、空载荷及服务重启后100次请求已实测通过。
有界原生Fuzzer、独立进程监控及单用例重放已在QNX实测通过：128例中34例正常应答、94例预期拒绝、0超时。
原生应用网关与会话限流对照也已实测：94个非法请求未转发；专用24例限流场景与无授权零转发场景通过。
运行中动态撤权及异常授权配置已实测：两轮各24例，均8次正常转发、16次拒绝，恢复授权后可正常请求。
受控服务退出与恢复已实测：停止前后各10次正确应答，停机窗口设备不可用，独立只读OS探针覆盖全过程。
**故障隔离验证与伙伴复现尚未完成。**
本项目的课程适配评估为“方向符合，条件性建设”；教师审批仍待完成，QNX环境已具备。

## 从这里开始

1. 阅读 [项目工作流](docs/项目工作流.md) 和 [适配评估](docs/项目适配评估.md)。
2. 在主文件夹中使用 Python 3.10 或以上版本，无第三方运行依赖：

```powershell
python scripts/check_environment.py
python -m unittest discover -s tests -v
python -m ipcsec demo
python -m ipcsec calibrate
python -m ipcsec replay --case-id CASE-0001
```

运行会创建 evidence/runs/<run_id>/，包括 cases.jsonl、results.jsonl、summary.json、manifest.json。
每次运行创建新目录，不覆盖旧证据。重放建立新运行，保留源用例内容与固定逻辑时钟。
模拟结果仅说明软件管线在模型中的行为；模拟异常不是真实QNX Crash。

## 目录入口

docs/ 存Intent、规格、ADR、计划、工作流及课程映射；ipcsec/ 存主机模拟实现；
native/qnx/ 存QNX接口协议草案与接入说明；configs/ 存注册范围与试跑参数；
eval/ 存验收及评价器校准样例；evidence/ 存运行事实；review/ 存审查与签署；
release/ 存启动恢复交接；tests/ 存回归；scripts/ 存环境及索引检查。

实际结构及每个目录职责见 [项目结构](docs/项目结构.md)。
## QNX原生最小链路

详见 [原生运行说明](native/qnx/README.md) 与 [本次验证记录](review/native-milestone.md)。

```powershell
./scripts/Build-QnxNative.ps1
./scripts/Deploy-QnxSmoke.ps1 -TargetAddress <本机新建QNX虚拟机IP>
python scripts/verify_native_evidence.py
```

首次建机使用Build-QnxVm.ps1；启动使用Start-QnxVm.ps1，网络模式须按本机已有虚拟网卡选择。
真实结果位于evidence/native-runs/，与主机模拟的evidence/runs/分开。
VM磁盘、实验SSH密钥与编译产物都在build/内，不提交Git。
原生变异与监控见 [运行手册](release/native-fuzz-runbook.md) 和 [验证记录与TODO](review/native-fuzz-milestone.md)。

```powershell
./scripts/Deploy-QnxFuzz.ps1 -TargetAddress <登记的QNX虚拟机IP> -Count 128
python scripts/verify_native_fuzz_evidence.py evidence/native-fuzz-runs/20261017T122327Z-0b2f7718
```

变异证据位于evidence/native-fuzz-runs/。本轮仅说明自建服务的输入处理及进程存活，隔离结论保持INCONCLUSIVE。
防御对照与最新TODO见 [原生防御里程碑](review/native-defense-milestone.md)。全量证据检查会保留并报告历史失败，不能把全目录报告当成全部通过。
动态撤权与当前TODO见 [授权验收记录](review/native-authorization-milestone.md)。
最新恢复结果见 [恢复验收记录](review/native-recovery-milestone.md) 和 [恢复运行手册](release/native-recovery-runbook.md)。
受控暂停超时已在专用gate检查点下实测通过：约2.002秒返回ETIMEDOUT，同PID恢复；见 [暂停超时验收](review/native-stall-milestone.md)。此前失败保留在 [历史问题记录](review/native-stall-issue.md)。
课堂准备入口：[证据索引](review/evidence-index.md)、[演示讲述顺序](release/classroom-demo.md)。

## 本地交接与课程提交

E2候选和回滚演练：`python -m ipcsec.change_rehearsal run`，随后以打印的目录执行`python -m ipcsec.change_rehearsal verify --folder <目录>`。默认配置仍为10，候选仅为模拟，不是正式批准。用户已选择只计放行请求，主机修复及21例回归通过。E3独立入口见[审查指南](release/e3-review-guide.md)，内部[计数语义Finding](review/findings/INT-F-01-rate-accounting.md)待独立复核。

```powershell
python -m ipcsec.handoff audit
python -m ipcsec.handoff package
python -m ipcsec.handoff verify-bundle --archive <生成的ZIP路径>
```

打包输出到build/handoff/新目录，保留当前源码快照和原始证据，排除VM、SDK、二进制和SSH私钥。包内技术审计与课程Gate分开，历史失败不会隐藏。
交接说明见[伙伴复现](release/partner-reproduction.md)、[提交清单](release/submission-checklist.md)和[报告草稿](release/course-report-draft.md)。DeepSeek构造校准v2为10/10、有限真实材料审查v2为3/3，旧失败保留，见[校准报告](review/deepseek-calibration-milestone.md)。正式Change/E3、独立人工校准、教师批准、伙伴复现及个人签署仍待完成。
