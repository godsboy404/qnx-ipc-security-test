# 项目规格 draft 0.1

状态：待教师批准。模型载荷为ECHO、declared_length、offset、flags、payload。
模拟协议：payload上限64字节，declared_length等于实际字节，offset在0至实际长度之间，flags为0。
QNX系统消息封装尚未定稿，当前应用载荷不允许直接发送到任意resource manager。
实施更新：首个原生切片已采用自定义devctl ECHO，16字节应用头加实际payload；仅适用于自建/dev/ipcsec-lab。
该选择是当前工程实现，不代替教师对课程规格的批准；原生合法路径已实测，变异及隔离尚未验收。

| ID | 强度 | 要求 |
| --- | --- | --- |
| SEC-01 | MUST | 未登记、未授权或撤权目标不执行；真实发送逐次核权限 |
| IPC-01 | MUST | 合法请求返回可预测内容，QNX路径完成100次记录 |
| FUZ-01 | MUST | 边界、字段、组合变异具有固定种子和可保存语料 |
| SEC-03 | MUST | 非法类型、长度、offset、flags拒绝且不转发 |
| SEC-04 | MUST | 每会话有效请求窗口(now-1000,now]，初始上限10，超额拒绝 |
| OBS-01 | MUST | 每次运行记录源、配置、用例、结果、来源与预算，旧证据不改写 |
| ISO-01 | MUST | timeout不推断crash；缺独立目标、client、peer、service、system、recovery观测为未知 |
| REL-01 | MUST | 伙伴可依据说明启动、重放、重置、恢复并解释限制 |

## GWT场景

- GWT-P01 / IPC-01：给定ECHO和ping有效载荷，当发送，则正常应答且记录实长4。
- GWT-P02 / SEC-03：给定空载荷及声明0，当发送，则合法；不能把0长度默认视为攻击。
- GWT-N01 / SEC-03：给定声明65实长4，当启用防御发送，则BLOCK且target_outcome为NOT_SENT。
- GWT-N02 / SEC-03：给定offset为负，当发送，则BLOCK且不更改目标状态。
- GWT-A01 / SEC-03：给定非法type、超长与非法flags组合，当发送，则拒绝，不为声明的大长度分配内存。
- GWT-A02 / SEC-04：给定同会话同窗口前10个有效请求，当第11个到达，则RATE_LIMIT，其他会话仍可通过。
- GWT-A03 / SEC-01：给定未登记目标，当发起运行，则拒绝且不发送。
- GWT-U01 / ISO-01：给定缺独立系统探针，当只有超时或模拟异常，则INCONCLUSIVE，不计算隔离成功率。

性能阈值：待QNX实测基线和教师批准，不编造P95目标。模拟逻辑时间不当作真实运行延迟。
事实：存在主机模拟。假设：可取得QNX教学环境。决策草案：自建目标与应用网关。
未决：原生devctl封装、架构、探针权限与授权责任人。原生实验均被这些未知阻塞，主机模拟不阻塞。
