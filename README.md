# QNX IPC 安全测试课程项目

课程版：单个自建教学资源管理器的 IPC 对抗性测试与防御验证。

当前完成的是项目工程资产、可运行的主机模拟最小链路与QNX接入接口。
**尚未完成QNX交叉编译、真实资源管理器、真实IPC、进程监控或隔离验证。**
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
下一步任务为TASK-01：在合法授权的QNX 8.0实验机上验证工具链与合法请求往返。
