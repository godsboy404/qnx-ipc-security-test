# Harness清单

2026-10-22，适用ipcsec-spec-draft-0.3；本轮只做文档整理、本地回归和档案核验。

## QNX实验运行器与主机模拟

| 项目 | 主机模拟 | QNX原生实验运行器 |
| --- | --- | --- |
| 入口 | ipcsec/runner.py、configs/lab.json | native/qnx、scripts/Deploy-Qnx*.ps1、configs/native-lab.json |
| 目标 | SimulationTarget，非真实QNX | 本机授权VM内自建/dev/ipcsec-lab |
| 预算 | 配置max_cases=100；四场景400例是计划口径，不是原生批次 | 常规默认128/最多200；实际payload最多65字节；合法上限64 |
| 专用场景 | CH-01模拟10/5/10，默认仍10 | rate24；authorization24；deny历史16；退出恢复20次ECHO及停机open检查；暂停22次devctl尝试含gate及一次超时 |
| 时间 | 受控逻辑时间，不作为延迟 | 每次IPC2秒、监督15秒、主机45秒；动态授权握手2秒 |
| 防御 | 字段及会话窗口模型 | v2客户端应用网关，8会话、1秒最多10次ALLOW；baseline仍执行范围检查 |
| 观测 | cases/results/manifest | 目标审计、waitpid、peer；恢复期间有限uname及只读/proc探针 |
| 恢复 | 新实例、新run | 仅回收本轮子进程；先SIGCONT再清理暂停者；现有同名设备不接管 |

暂停使用显式controlled-pause及gate检查点，接收审计应匹配前后20次成功请求加1次gate；多余延迟交付判失败。暂停期间不访问设备作状态探针，可见性记null。6秒SIGALRM是异常恢复兜底，触发必须判FAIL，不是2秒截止通过。

快照恢复、退出重启和gate发送侧超时已有历史记录；未覆盖全部取消语义及完整系统服务健康。操作见../release/native-fuzz-runbook.md与native-recovery-runbook.md；本轮不执行。

## 开发/评价Agent Runtime Harness

| 控制项 | 规则 |
| --- | --- |
| 文件与工具 | 依本会话工具权限和项目范围，仅本仓库必要修改；不执行陌生目标代码、不打印密钥 |
| 网络与模型 | 本轮模型API调用预算0、VM操作0；既有有限摘要外发授权不扩大为完整日志外发 |
| 材料 | 按Req读取最小代码/文档/证据；模型只看已批准有限packet，输出为待人工复核草稿 |
| 失败与停止 | 未知目标、预算耗尽、权限不足、同类关键失败三次则保存证据并停止相关动作；其他可完成工作继续 |
| 恢复 | 文档变更使用可评审Diff及契约快照；运行新建目录；不覆盖旧证据、不擅自reset或提交 |

目标watchdog不控制Agent工具权限、模型费用或外发。评价器v2真实材料门未通过，不追加付费试错；ADR0002决定继续适用。

## 权威与冲突处理

| 信息/冲突 | 权威来源与处理 | 确认角色 |
| --- | --- | --- |
| 范围、授权 | 当前用户明确指示及intent；历史批准限其范围 | 环境所有者/项目负责人；新增范围需明确决定 |
| 课程要求、最终验收 | 实际教师要求与批准记录；选题同意不等于规格/验收确认 | 教师；AI不代签 |
| 当前行为 | specification的Req；代码不一致登记Finding，不自动修改规格迁就实现 | 项目成员确认业务语义，课程影响按教师要求确认 |
| 运行事实 | 具体evidence Run、manifest、原始日志；review负责解释 | 验证成员，独立复现由伙伴实际执行 |
| Change | 明确决定、Req影响、候选/回滚证据；CH-01仍候选 | 项目负责人；需要课程批准的事项按实际要求执行 |
| 模型意见 | 仅建议；可信登记预检不是真实性或教师签署 | 人工复核者 |

假设、责任及材料可见性见open-questions；当前状态表仅在../release/continuity.md维护。
