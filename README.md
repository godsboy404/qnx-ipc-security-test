# QNX IPC 安全测试课程项目

课程版：单个自建教学资源管理器的 IPC 对抗性测试与防御验证。

当前完成项目工程资产、主机模拟链路，以及QNX 8.0 x86_64虚拟机上的真实devctl ECHO链路。
Hello、100次合法请求、空载荷及服务重启后100次请求已实测通过。
**完整Fuzzer原生接入、独立进程监控、防御对照和故障隔离验证尚未完成。**
本项目的课程适配评估为“方向符合，条件性建设”；教师审批及QNX环境门仍为待完成。

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
下一步为原生监控与测试Harness完善，随后将有界变异接入自建目标。
