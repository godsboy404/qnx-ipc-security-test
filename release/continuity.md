# 连续性与移交

Current State：文档、主机模拟及真实QNX 8.0 VM上的合法devctl ECHO已跑通。
Last Verified Version：主机回归见review/verification.md；原生版本和证据哈希见review/native-milestone.md及其完整索引运行manifest。
Open Failures：独立探针、故障隔离、原生Fuzzer、防御对照、教师批准及伙伴签署未完成。
Decisions：自建单目标；模拟与原生分开；不把超时当崩溃。
Recovery Baseline：IPC-Ready-20261015快照已创建并验证恢复，review/snapshot-restore.txt有实际输出。
Next Safe Action：完善原生Harness和独立监控，再按预算接入变异。最新里程碑见review/native-milestone.md。
Human Questions：教师接受状态、组员实名、目标授权。
Do Not Repeat：不要用模拟结果证明QNX隔离，不要先开发全系统拦截。
