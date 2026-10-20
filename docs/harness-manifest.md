# Harness清单

当前审批更新2026-10-19：教师已同意选题，由用户明确转述，见review/teacher-approval-20261019.md。下文选题Gate待确认表述为历史记录；限定实验授权不扩大，Spec冻结草案、CH-01提案、最终课程验收各自跟踪。

同日后续决定：用户选择仅放行请求计数，模拟已修复，原生策略不变；INT-F-01的21例主机回归无差异，独立复核pending。新候选证据evidence/change-runs/20261017T144728Z-3cc92703/；下文OPEN/待选择描述为修复前检查点。

2026-10-17候选演练更新：ipcsec.change_rehearsal仅用主机SimulationTarget，以同一22例逻辑时序执行10/5/10三组并记录源码身份、配置和哈希。configs/ch01-candidate.json不会覆盖默认配置，formal_E2=false。scripts/Reproduce-RateAccounting.py是21例本地Python/原生主机判定器对比，不调用VM，不宣称QNX实测或正式E3。内部Finding INT-F-01为OPEN，等待业务语义选择与独立复核。

Runtime：当前Python单进程模拟，单槽、确定性语料；无网络、无shell调用、无生产系统访问。
新增原生合法路径：用户授权的新建QNX 8.0 VM、自建/dev/ipcsec-lab、项目专用SSH密钥；只运行合法ECHO及自建服务重启。
原生每次请求2秒SEND/REPLY超时，主机执行截止45秒；阻塞场景本轮未测试。VM使用已有VMnet8，移除Guest默认路由。
Project：本目录AGENTS、docs、configs、tests、eval、evidence、review和release。
验证命令：README四条命令均需可运行；QNX不提供伪可执行命令，见native/qnx/README.md待实现项。
预算：每场景100例、4场景，总400例；真实测试时间与API成本待试跑批准。
允许：本仓库读写、主机模拟、回归。禁止：真实系统扫描、敏感数据、修改旧证据。
需批准：教师Intent Gate、故障注入、变更CH-01和发布。用户已明确授权创建本机实验VM、部署Hello与自建合法IPC；不据此声称教师审批完成。
Stop：未知目标、原生后端误调用、同类关键失败三次、预算耗尽。
恢复：模拟新实例新run；原生依赖快照和外部watchdog，尚未完成。
上下文：全局入口仅地图与规则；任务按需读取Spec、ADR、代码和测试；日志限必要字段。
权威：批准的课程契约优先于目标README；运行事实在evidence；教师批准和签署在review。
配置评估：每改规则/限流/权限，重跑相同语料、窗口边界和校准样例，报告结果及成本变化。

更新2026-10-17：用户已授权独立监控和有界原生Fuzzer。当前原生预算以configs/native-lab.json为准：默认128/最多200例，单次IPC 2秒，监督15秒，主机45秒。Runtime新增独立target、worker、monitor、peer四个进程。历史400例为实验计划，非本轮实际执行量。快照恢复已演练，见review/snapshot-restore.txt；故障后恢复尚未验收。原生数据、哈希和重放说明见release/native-fuzz-runbook.md。

原生客户端网关更新：schema_version=2支持baseline/defense、八个受限会话、真实1秒窗口内10次合法请求尝试。每次转发前读取authorization.txt；服务端独立接收审计与客户端记录逐条核对。会话来自有界实验语料，不等于可信身份。网关可被直接访问设备的程序绕过，不宣称内核级拦截。专用rate语料24例、等待1100ms；deny场景16例；失败实验保留原始证据。操作与最新事实见review/native-defense-milestone.md。

动态授权更新：authorization专用24例由独立监督进程执行每请求授权计划，写入/移除文件、读回并记录后才确认客户端下一次权限读取；确认截止2秒，监督15秒和主机45秒截止保留。两轮各8转发/16拒绝及缺文件单例重放通过，原始事件、字段和服务端审计分开保存。只验证同步请求边界，不撤销在途IPC。见review/native-authorization-milestone.md。

恢复切片更新：lab-recovery独立启动本轮服务、只读OS探针及三个阶段客户端，最多20次合法IPC和1次停机open检查；仅向自己启动的服务PID发送SIGTERM，waitpid确认后重启新PID。探针执行uname和只读stat(/proc)，不发送系统服务变异消息。IPC 2秒、监督15秒、主机45秒；主动停机观察约200ms，不当作纯启动延迟。既有设备拒绝接管，结束只回收自己启动的子进程。证据在evidence/native-recovery-runs/，完整隔离保持未知。

暂停实验状态：4轮均未验收，后3轮6秒SIGALRM兜底恢复并清理；按连续失败规则停止真实注入。最新修复仅在显式controlled-pause模式用gate ECHO触发接收前暂停，计划22次IPC尝试；尚未在QNX验证。暂停时禁止访问目标设备，probe仅做独立只读OS检查。失败原始目录、首轮后续恢复记录和人工问题见review/native-stall-issue.md。

用户再次明确要求继续后，gate检查点版本已在20261017T130224Z-8ed73897验证通过，原4轮失败不变；默认停止/重启回归20261017T130304Z-d6c6072a通过。当前可验收限定发送侧超时与同PID恢复，完整隔离仍未知。见review/native-stall-milestone.md。
