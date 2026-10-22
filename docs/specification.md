# 规格说明：QNX IPC Security Lab

契约ID：ipcsec-spec-draft-0.3；状态：project_draft，首轮提交评审稿。日期2026-10-22。本文整理现行行为，不新增功能或教师批准。整理基线17a4a37；旧契约逐字节快照及登记迁移见[版本记录](contracts/README.md)。需求来源见[需求分析](requirements-analysis.md)。

## 1. 目标、范围及非目标

对象为已登记lab-resmgr-01，仅对应授权自建QNX8 x86_64 VM内/dev/ipcsec-lab。主机模拟与原生批处理分别执行和归档；Python QnxTransport逐请求接口不提供可用实现，不允许静默回退。原生服务端有边界检查，客户端应用网关另做策略检查。

本规格不承诺内核钩子、全系统IPC拦截、可信会话身份、在途IPC撤销、系统服务攻击、漏洞崩溃发现或完整系统隔离。受控退出/暂停仅验证限定恢复行为。

## 2. 接口与结果

合法请求为ECHO，declared_length等于实际payload字节数，范围0至64；offset为0至实际长度；flags为0。空载荷合法。原生LAB_DCMD_ECHO封装16字节应用头（uint32 operation=1、uint32 declared_length、int32 offset、uint32 flags）及实际payload；容量80字节，不是任意资源管理器通用协议。声明长度不构成已接收字节的证明。

原生目标核对实际接收大小、nbytes、消息长度及回复容量，再读取头和复制有限字节；畸形测试实际payload最多65字节。合法应答返回请求头及payload，非法输入返回对应错误。offset只是合法性字段，当前不表示截断回显。

客户端决策为ALLOW、BLOCK、RATE_LIMIT、SCOPE_DENY。v2原生测试的baseline保留目标/授权/会话范围检查；defense再检查结构及频率。ALLOW表示获准尝试发送，不保证应答成功。网关拒绝时forwarded=false、target_outcome=NOT_SENT；本地返回码-1是哨兵，不是目标errno。真实发送结果区分REPLY、ERROR_REPLY、TIMEOUT；退出证据另由监督进程确认。

## 3. 当前需求

| Req | 强度 | 行为与判定要求 |
| --- | --- | --- |
| SEC-01 | MUST | 未登记、未授权、授权文件缺失/坏格式/目标不匹配时不执行下一请求。v2原生客户端逐请求检查私有authorization.txt；动态授权在监督进程变更读回并握手确认后生效，不取消在途IPC。恢复授权不清空限流历史 |
| IPC-01 | MUST | 合法ECHO返回可预测内容；原生合法基线记录100次ping、空载荷及重启后往返；逐条核对返回，具体历史次数不作为每次新运行的固定预算 |
| FUZ-01 | MUST | 固定种子生成边界、字段与组合变异，保存实际语料及顺序，支持单例重放；重放单例不等于重现完整会话历史 |
| SEC-03 | MUST | defense路径拒绝非法操作、长度、offset、flags且不调用devctl；用接收审计核对无转发。服务端独立做实际长度校验，baseline发送畸形输入不等于关闭服务端检查 |
| SEC-04 | MUST | defense中每个实验会话窗口(now−1000ms, now]最多10次结构有效且获准转发的请求。非法、撤权、限流拒绝不追加计数、不延长窗口。计数在ALLOW决策阶段、实际IPC之前发生，随后超时/错误不返还槽位。原生使用CLOCK_MONOTONIC及八个会话槽，主机使用受控逻辑时间；会话标签不是认证身份。CH-01的5仅候选模拟，未采用 |
| OBS-01 | MUST | 每轮记录源/配置/输入/结果/预算与后端；原生审计关联顺序、有界字节和目标PID。保存manifest及哈希，拒绝旧版本冒充当前；接收审计仅覆盖登记处理路径，不推断全部系统流量 |
| ISO-01 | MUST | 不以TIMEOUT推断crash；缺独立目标、client、peer、service、system或recovery所需观测时完整隔离为INCONCLUSIVE，隔离成功率不计算。有限存活与只读OS探针不证明完整系统健康 |
| REL-01 | MUST | 提供启动、重放、重置、恢复、限制和伙伴步骤；受控退出重启与同PID暂停恢复分别留证。伙伴独立接管需其实际新运行及记录；作者自检不能代替 |

## 4. GWT及验收方式

| 场景 | Given / When / Then | Req |
| --- | --- | --- |
| GWT-P01 | 已授权ECHO ping；发送；返回相同载荷并记录实长4 | IPC-01 |
| GWT-P02 | 空payload且声明0、offset0、flags0；启用defense；结构检查允许，仍服从授权/频率规则 | SEC-03 |
| GWT-N01 | 声明65实长4；defense判定；BLOCK且NOT_SENT | SEC-03 |
| GWT-N02 | offset负数；defense判定；BLOCK且目标无该次接收 | SEC-03 |
| GWT-A01 | 非法操作/超长/flags组合；校验；拒绝且不按声明长度分配 | SEC-03、FUZ-01 |
| GWT-A02 | 同会话同窗口已放行10例；第11例到达；限流，其他会话可通过，边界过期后恢复 | SEC-04 |
| GWT-A03 | 未登记或撤权已确认；下一请求；拒绝且不发送 | SEC-01 |
| GWT-U01 | 只有超时/模拟异常或缺独立探针；作隔离判断；INCONCLUSIVE | ISO-01 |
| GWT-R01 | 本轮自建服务受控SIGTERM退出；重启；新PID正确应答，停机open错误单独记录 | REL-01、ISO-01 |
| GWT-R02 | 显式gate回复后服务SIGSTOP且waitpid确认；合法devctl的2秒截止到期；记录超时、SIGCONT、同PID恢复及接收审计 | REL-01、ISO-01 |

检查入口、证据Run及源身份见[验收矩阵](acceptance-matrix.md)。逻辑时钟端点自测不冒充实时时钟精确1000ms实验。恢复/暂停的预期接收条数、清理和停止条件见[Harness](harness-manifest.md)。

## 5. 限制、假设及确认事项

默认预算和期限见Harness；当前运行参数不表示性能目标。性能阈值、重复Trial及人工成本口径待项目成员/教师确认；不编造P95/P99标准。完整系统隔离未知，回复侧完整取消语义未穷尽。

私有授权文件可被有写权限者修改，不是防篡改凭证；客户端网关可被设备直接访问者绕过。当前没有服务端可信身份绑定或完整策略强制执行承诺。

既有false_positive_rate是结构合法输入的非ALLOW比例，不能解释成策略错误误拒率；改进指标仅为候选定义，尚未改计算实现，见experiment-plan。评价器v2真实材料门未过，模型只提供待复核草稿。选题同意、规格确认、正式事件及最终验收分别记录。

## 6. 历史与追踪

旧稿见[0.2快照](contracts/ipcsec-spec-draft-0.2.md)；限流决定见[原决定](../review/DEC-SEC04-rate-accounting.md)和[ADR0003](adr/0003-rate-accounting.md)；原生演进及失败修复见[证据索引](../review/evidence-index.md)、[暂停问题](../review/native-stall-issue.md)和[修复里程碑](../review/native-stall-milestone.md)。历史Run保持原manifest身份，整理不赋予新契约资格。后续变更需记录Req影响、理由、检查与版本，不修改历史证据。
