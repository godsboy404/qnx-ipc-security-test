# 课堂实验与证据索引

更新：2026-10-17。各结果仅归属对应运行manifest中的源码与二进制版本，不能把不同版本的记录拼成一次新运行。下表原生记录由本机SSH runner产生，伙伴独立复现和人工签署仍pending。

| 能力 | 入口与主要事实 | 尚未证明 |
| --- | --- | --- |
| 真实合法IPC | native-milestone.md；evidence/native-runs/20261015T104537Z-afa1f753，100次ping、空载荷、重启后100次ping | 生产环境性能阈值 |
| 有界原生变异 | native-fuzz-milestone.md；20261017T121606Z-e29291df，128例中34应答、94预期错误 | 漏洞发现或覆盖全部协议 |
| 网关防御对照 | native-defense-milestone.md；baseline 20261017T122304Z-ad2730f7、defense 20261017T122327Z-0b2f7718，同语料128例；94非法不转发，14合法被限流，20应答 | 不可绕过的系统强制拦截 |
| 会话限流 | 同上；baseline 20261017T122624Z-166ba568、defense 20261017T122645Z-89c9b79f，24例中2次超额拒绝 | 不可信客户端身份认证 |
| 动态授权 | native-authorization-milestone.md；20261017T123348Z-63e1b79f与20261017T123421Z-e4e1c71d，各24例，8转发16拒绝 | 任意并发撤权或取消在途IPC |
| 受控退出与恢复 | native-recovery-milestone.md；新共享版本回归20261017T130304Z-d6c6072a，前后各10次应答，停机ENOENT，新PID恢复 | 非预期crash或全部恢复场景 |
| 真实暂停超时 | native-stall-milestone.md；20261017T130224Z-8ed73897，约2.002秒返回ETIMEDOUT=260，同PID恢复，接收审计21条 | 回复侧完整取消语义、全系统隔离 |

运行根目录：native-runs、native-fuzz-runs、native-recovery-runs、native-stall-runs均位于evidence/。成对比较另存evidence/native-comparisons/，连接双方manifest哈希。具体命令见release/的运行手册。
历史暂停失败4轮保留在native-stall-issue.md，全量历史检查不得掩盖这些失败。演示与最终验收应明确指定被核验运行，不能删除失败目录使全历史显示通过。

技术结果已可支撑单目标课程演示。课程教师Gate、伙伴干净环境复现、真实姓名贡献与AI使用签署、最终发布审查仍需完成；完整系统隔离继续为INCONCLUSIVE。

## 2026-10-19新增工程证据

新Schema与登记预检、三种推理配置的负结果及停止决定见20261019-evaluator-and-handoff.md。模型比较在evidence/model-comparisons/20261019T125335Z-df02bb00/，各快照原始响应/耗时在evidence/model-review-runs/20261019-*。当前并未取得新格式真实材料的整体通过；不能替换10月17日历史结果或声称伙伴复现。选定模拟原始run由configs/handoff-evidence.json逐项列明并独立重算，仍不属于QNX证据。
