# 新聊天接续说明

截至2026-10-19；这是仓库内的可更新接续索引，不是软件自动同步聊天记忆的保证。新会话先核对实际文件、Git状态和最新证据，不能把本文件日期当作实时状态。

## 工作区与读取顺序

仓库：`D:/Users/Downloads/QNXsec/qnx-ipc-security-test`。先读AGENTS.md及其规定的四份基础文档，再读release/continuity.md、submission-checklist.md、review/roles.md、review/20261019-personal-rounds-recheck.md。本文件只提供摘要，冲突以具体版本、运行档案和最新用户确认处理。

用户习惯中文沟通，希望授权范围内持续推进；不要反复询问已确认事项，也不要把AI自检记为学生或独立伙伴实际操作。每轮说明变更、核验及剩余事项。

## 人员与批准

本组：张润泽（用户）、陈卫吉。互评组：邓一帆（用户报告1人）。教师已同意选题，来源为用户2026-10-19明确转述，见review/teacher-approval-20261019.md；不是CH-01具体采纳、逐项Spec批准或最终成绩验收。

R1张润泽实现摘要展示，陈卫吉验证；R2陈卫吉实现耗时语义检查，张润泽验证。用户报告两轮完成并签署，代码复查81项通过。任务卡含本人解释，日志与修改身份引用、冻结留存说明仍待收尾。邓一帆独立互评尚无实际执行记录，不与组内轮换混淆。

## 工程现状

已有QNX8 x86_64自建devctl ECHO资源管理器/客户端、有界Fuzzer、客户端应用网关、会话限流、逐请求授权、独立监控/peer/接收审计、SIGTERM重启及SIGSTOP/SIGCONT发送侧2秒超时恢复。主机模拟与原生分开。

关键历史结果：合法100+空1+重启后100；baseline128为34正常/94预期错误；相同defense128为94BLOCK、14RATE_LIMIT、20应答，接收端20；rate24为22应答/2限流；authorization24为8应答/16拒绝；暂停约2.002秒ETIMEDOUT=260，同PID恢复。混合语料限流数量受真实时序影响，不强求每次14。

只计有效放行请求，拒绝不延长窗口；窗口(now-1000ms,now]，默认10。CH-01候选5只完成模拟10/5/10及回滚，未正式采用。客户端网关可绕过，不是内核强制防御。timeout不等于crash；系统隔离保持INCONCLUSIVE；回复侧完整取消语义未穷尽。

DeepSeek已接入，密钥仅从环境变量读取，不能打印或索取。Schema v2区分来源、后端和强度，固定登记预检已实现。构造校准通过，真实材料门未通过，候选路由仅1/3与AI预期一致；旧Schema v1的3/3不能转移资格。独立真值仍缺，模型只作待复核草稿。不要无止境付费调参，参见ADR0002。

## 版本与证据

当前最新复查81 tests通过，历史报告核验与handoff审计PASS。历史run131706保存76 tests，133034保存79 tests，不能改写。工作树有多轮未提交改动，先git status；不擅自commit/push，不reset或覆盖学生改动。

重要入口：

- 用户自检：evidence/local-check-runs/20261019T131706Z-eae3eef7/。
- 后续个人任务阶段自检：evidence/local-check-runs/20261019T133034Z-69f9f883/。
- 所选原生与模拟：configs/handoff-evidence.json。
- 模型真实输入登记：configs/review-registry.json；docs/specification.md哈希固定，不能随文档同步悄悄改掉。
- 最近已核验旧包：build/handoff/20261019T131126Z-cc2e526c/qnx-ipc-security-test-handoff.zip，SHA256为07522A522D9AB5CD7CE3D084579896D7FB6C3C73ECF30CE7912AFB527175269F。早于个人修改及本文件，不能冒充最新成果包。

原始evidence、历史报告和旧包保留原样；最新说明在当前入口更新。build中的AI复核临时数据不是学生原始Transcript。

## 环境与核验

Windows专业版26H2 build26300.9711 x64；用户Python3.11.9；工具PowerShell7.6.5，Windows PowerShell5.1.26100.9711；QNX SDP8.0安装于C:/Users/zrz51/qnx800；VMware26.0.0 build25388281；历史Guest QNX8.0.0 x86_64。新会话重新核查可用性，不能假定VM已开机或沿用旧IP。

正常PATH可运行：python -m unittest discover -s tests -v；python -m ipcsec.local_check run；python -m ipcsec.local_check verify --folder <新run>；python -m ipcsec.handoff audit。local_check覆盖demo/calibrate等八步，产生新证据，不是独立伙伴复现。

工具Python备用：C:/Users/zrz51/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。Git备用：同一dependencies/native/git/cmd/git.exe。这都是本机路径，换机应重新确认。

## 权限边界与下一步

既有实验授权限本机自建VM、/dev/ipcsec-lab、有界变异、私有逐请求授权和本轮自建进程受控恢复；不覆盖系统服务、第三方目标。模型外发曾获准仅三份有限自建实验统计/哈希/Claim摘要，不自动扩展到新项目、完整日志或敏感材料。

当前剩余：个人任务引用收尾；邓一帆独立复现及Finding闭环；正式E1成本/取舍、E2、E3；评价器独立真值/保留集/隔离环境；统计误拒指标语义；章节01作业记录（若单独收）；最终冻结、打包、演示和签署。

用户开始咨询本科毕设升级，方案见docs/thesis-evolution-plan.md。该文件为建议，尚未授权开展新实验，也不等于学校毕设题目已审批。不要把课设未闭环事项靠改题为毕设隐藏。
