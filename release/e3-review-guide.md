# E3独立审查执行材料

状态：READY_FOR_REVIEW，独立执行NOT_RUN。教师已同意选题（见review/teacher-approval-20261019.md），最终课程验收与签署pending。AI生成的内部Finding不冒充伙伴Finding。

## 交给伙伴的材料

主入口为AGENTS.md、docs/intent.md、specification.md、acceptance-matrix.md、harness-manifest.md。技术报告release/course-report-draft.md，证据范围review/evidence-index.md，恢复步骤release/partner-reproduction.md。交接包的SOURCE-SNAPSHOT与PACKAGE-MANIFEST限定当前版本；旧manifest限定各自历史版本。

## 执行顺序

1. 记录伙伴实名、时间和交接ZIP哈希；在干净目录解压，不接收作者SSH私钥或VM/SDK副本。
2. 先执行unittest、demo、calibrate、handoff audit；calibrate为确定性基线，不代表模型校准。
3. 执行change_rehearsal verify核对候选22例三组证据，再新运行一次演练，检查第5/6次、其他session、1000ms过期、非法输入不占预算及回滚。候选不等于教师批准E2。
4. 对review/findings/INT-F-01-rate-accounting.md自行复现；确认最小序列、证据层级和影响，决定是否登记为伙伴新Finding。不要直接签署AI记录为本人发现。
5. 检查三个Claim：SEC-03只覆盖该轮自建服务网关；OBS-01哈希只证明本地一致性；ISO-01完整系统隔离为未知。对任意“全系统拦截/隔离保证”“100%准确率”“timeout等于crash”要求原证据或提出Finding。
6. 如需独立QNX复现，使用伙伴合法SDK、登记目标与独立密钥，按partner-reproduction.md执行，不扫描或更换目标。真实系统变异和故障注入不由本材料授权。
7. 伙伴自行编写未暴露的模型校准变体和人工答案；先冻结哈希，答案不进模型请求，遵守10次/快照预算。供应商API不得发送未经授权的新项目或敏感材料。
8. 用review/FINDING.md记录问题，作者逐项接受/驳回并附理由及新证据；伙伴复核后才关闭。填写review/partner-reproduction-record.md实际结果。

## 人工审查记录模板

审查人/组别：待本人填。开始与结束时间：待填。目标ZIP SHA256：待填。范围及版本：待填。

| Claim或Finding | 伙伴执行证据 | 结论/级别 | 作者回应 | 复核及关闭 |
| --- | --- | --- | --- | --- |
| SEC-03 | NOT_RUN | pending | pending | pending |
| OBS-01 | NOT_RUN | pending | pending | pending |
| ISO-01 | NOT_RUN | pending | pending | pending |
| INT-F-01独立复现 | NOT_RUN | pending | pending | pending |
| CH-01候选/回滚 | NOT_RUN | pending | pending | pending |

工具只能生成建议；姓名、耗时、贡献、实际操作及最终签署由本人填写。伙伴提出的新需求先进入变更流程，不能改写旧证据。
