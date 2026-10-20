# 项目工程规则

先读 docs/intent.md、docs/specification.md、docs/acceptance-matrix.md 和 docs/harness-manifest.md。
新会话接续再读release/new-chat-handoff.md及release/continuity.md；前者为截至2026-10-19的索引，开始工作前核对当前Git状态与最新用户信息，不能把历史快照当实时状态。
2026-10-19用户明确转述教师已批准选题，见review/teacher-approval-20261019.md；选题接受事项已解除。Spec冻结草案和CH-01提案未据此视为逐项批准，最终课程验收仍pending。用户已授权本机QNX实验VM、自建IPC、独立监控和有界原生Fuzzer，不授权其他真实目标测试。下文教师Gate待确认描述为历史阶段记录。

- 主机模拟使用 ipcsec/，QNX原生适配使用 native/qnx/，不可混淆证据来源。
- 只测试明确登记并获授权的自建目标；默认不提供网络、任意Shell或系统服务测试接口。
- 测试配置、验收和源代码变更应关联Req ID；旧运行证据不可编辑或冒充新版本证据。
- 不能用timeout推断crash；没有独立探针时隔离结果必须为INCONCLUSIVE。
- 校验失败不得通过删除测试或降低规格解决；连续三次相同关键失败时保存证据并记录人工问题。
- 未经批准不进行生产部署、真实服务扫描、敏感数据接入或破坏性变更。
- 验证：python -m unittest discover -s tests -v；python -m ipcsec demo；python -m ipcsec calibrate。
- 原生代码已具备devctl ECHO合法路径。真实目标限定新建VM中的/dev/ipcsec-lab；每次IPC 2秒超时，Smoke主机截止45秒。
- 有界Fuzzer与独立监控已实测，见review/native-fuzz-milestone.md；系统服务和资源管理器崩溃注入不在本轮范围。扩大测试前检查授权、快照、重置及watchdog。
- 用户已要求继续原生应用网关和会话限流实践；仅在同一自建目标执行有界baseline/defense/rate/deny场景。教师选题已同意，最终课程验收仍pending。
- 动态授权场景仅由监督进程修改本轮私有授权文件，逐请求同步、最多24例；已验证撤权及缺文件等关闭路径，见review/native-authorization-milestone.md。不得把结果扩展为在途IPC可撤销或系统级强制隔离。
- 当前用户已要求继续自建服务受控退出与恢复：仅停止本轮创建的服务PID并重启，独立探针只做uname和只读/proc检查。此范围不覆盖系统服务攻击、漏洞崩溃注入或全系统隔离结论。
- 当前继续执行同一自建服务的受控SIGSTOP/SIGCONT与单次2秒IPC超时验证；仅操作本轮子进程，异常清理必须先恢复暂停进程。不扩展至系统服务或第三方目标。

模型可生成建议和候选代码。范围、业务语义、证据结论、签署由人决定。
