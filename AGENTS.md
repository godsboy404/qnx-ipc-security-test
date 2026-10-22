# 项目工程规则

先读docs/intent.md、docs/specification.md、docs/acceptance-matrix.md和docs/harness-manifest.md；接续读release/continuity.md及release/new-chat-handoff.md，核对实际Git状态，不把历史快照当实时状态。首轮材料入口release/first-round-submission.md。

模块：ipcsec/主机模拟、归档核验及评价器；native/qnx/原生服务、客户端、监督；configs/范围与登记；docs/契约和ADR；evidence/原始事实；review/解释及签署；release/交接。

- 只测试明确授权的自建目标。既有范围限本机VM内/dev/ipcsec-lab、有界变异、私有逐请求授权及本轮子进程受控退出/暂停恢复。系统服务、第三方目标和漏洞崩溃注入不在范围。
- 主机模拟与原生证据分开；timeout不等于crash，缺完整独立观测时系统隔离为INCONCLUSIVE。客户端网关可绕过，会话标签不是认证。
- 默认窗口1秒最多10次有效放行；拒绝不计数。CH-01的5仍候选模拟。变更关联Req，冲突登记，不删除检查或降低规格求通过。
- 旧evidence、历史review及模型档案不得改写。契约改变先快照、显式新ID/登记和核验，不转移旧评价资格；登记策略见docs/contracts/README.md。
- 教师选题同意来自用户转述；规格确认、正式事件和最终验收另行记录。AI不代填批准、贡献或签署。
- 连续三次相同关键失败，保存证据并停止相关动作；预算、授权和恢复边界见Harness。暂停进程清理先SIGCONT，仅操作本轮子进程。
- 不打印密钥，不擅自扩展模型外发；评价器v2真实材料门未过，仅草稿。本轮模型API调用0，不运行原生实验。
- 保留学生修改，不擅自commit/push/reset；当前整理产物待人工评审和冻结。

验证：python -m unittest discover -s tests -v；python -m ipcsec demo；python -m ipcsec calibrate；python -m ipcsec.handoff audit。作者统一自检python -m ipcsec.local_check run产生新证据，不等于伙伴复现。原生操作按release手册，先核对授权、目标、预算与恢复条件。
