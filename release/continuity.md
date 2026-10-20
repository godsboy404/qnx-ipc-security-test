# 连续性与移交

更新：2026-10-19。

Current State：真实QNX合法IPC、有界变异、客户端防御、会话限流、动态授权、受控退出/暂停恢复已归档。DeepSeek已接入；Schema v2分离后端/来源/强度，并增加固定本地档案登记预检。CH-01仅完成模拟候选，默认预算仍10。
Last Verified Version：最新代码复查81项主机测试通过、历史报告核验及证据审计PASS，见review/20261019-personal-rounds-recheck.md。历史运行各有manifest；131706记录76项、133034记录79项，不能改写为81。既有交接包20261019T131126Z-cc2e526c早于两轮个人修改，不能代表最新工作树，最终交付前须重新冻结与打包。
People and Personal Tasks：张润泽、陈卫吉；互评组邓一帆。R1张润泽实现/陈卫吉验证，R2陈卫吉实现/张润泽验证，用户报告已完成并签署；代码复查通过，任务卡含个人解释。记录见review/roles.md和review/personal-rounds/。仍需补修改身份与验证日志引用、如实说明条件冻结快照留存情况；不再笼统记个人任务未完成。
Open Failures：新Schema v2真实材料门未通过，工程取舍为NEEDS_MORE_EVIDENCE。完整系统隔离未知，回复侧完整取消语义未穷尽；模型校准不代替独立人工真值。正式E1、E2/E3、邓一帆独立复现/审查、最终提交签署仍待完成，与已报告完成的两轮个人任务分开跟踪。
Decisions：自建单目标；只计已放行请求，拒绝不延长窗口；运行后端、证据来源与强度分开；教师未批准事项不擅自N/A。
Recovery：已有IPC-Ready-20261015快照恢复证据及目标退出/暂停后的恢复记录，见对应原生手册。新实验产生新run，不覆盖旧目录。
Next Safe Action：补齐两轮个人任务的修改身份和验证日志引用；请邓一帆按release/partner-reproduction.md及e3-review-guide.md实际执行独立复核。按eval/real-claim-review-card.md形成独立人工判据，补正式E1成本/决策与E2/E3记录。新发布前运行handoff audit、冻结当前版本并重新打包。

Delivery Update：已增加统一作者自检ipcsec.local_check，20261019T131049Z-557d756c八步通过，含76项测试；原72项为此前检查点。新生成依赖随包核验。下一步实际执行顺序见release/final-execution-guide.md，阶段记录review/20261019-delivery-self-check.md。
Teacher Approval：2026-10-19用户明确转述教师已批准、同意，选题接受事项已解除，见review/teacher-approval-20261019.md；不等于最终课程验收、CH-01采纳或逐项规格签署。
Human Questions：正式事件与邓一帆独立互评的实际执行记录；最终提交签署；互评组1人安排按教师实际组织要求确认；独立评价工作区的隔离方案。
Do Not Repeat：不把主机模拟或本地重算叫作独立QNX复现；不以增加token上限隐藏失败；不自动执行陌生目标代码；不扩展全系统IPC拦截。
