# 连续性与移交

Current State：真实QNX合法IPC、有界变异、客户端网关、会话限流、动态授权、受控退出与发送侧超时恢复均有证据。交接草稿和包审计工具已备。
Last Verified Version：各原生结果归属各自manifest；当前源码以交接包SOURCE-SNAPSHOT.json冻结，不能由旧manifest哈希重建缺失的历史源码。最新索引review/evidence-index.md，课程缺口见release/submission-checklist.md。
Open Items：完整系统隔离未知；回复侧取消语义、正式E2/E3、评价Agent模型接入与真实材料校准、教师批准、伙伴复现和个人签署仍未完成。历史失败5轮保留，不与已通过修复版本混淆。
Decisions：自建单目标；模拟与原生分开；不把超时当崩溃。
Recovery Baseline：IPC-Ready-20261015快照已创建并验证恢复，review/snapshot-restore.txt有实际输出。
Next Safe Action：按partner-reproduction.md由独立结对组从新目录运行并记录；按submission-checklist.md完成正式课程环节。只读技术审计用python -m ipcsec.handoff audit，本地打包用python -m ipcsec.handoff package。
Human Questions：教师接受及正式事件要求、组员实名与实际贡献、独立结对组及签署。不能由AI代填。
Do Not Repeat：不要用模拟结果证明QNX隔离，不要先开发全系统拦截。
