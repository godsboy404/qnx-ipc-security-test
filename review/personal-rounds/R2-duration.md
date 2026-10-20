# R2：自检耗时字段语义校验

Req：OBS-01。计划实现者陈卫吉，验收条件制定与验证者张润泽。状态：COMPLETED_REPORTED；AI复核通过，人工签署由用户报告已完成，原始签名附件未入库。

以下为AI候选条件，由张润泽先审定后交陈卫吉实现：

- elapsed_ms接受有限、非负的int/float，包括0；拒绝负数、True/False、字符串、null、NaN及正负Infinity。
- 不修改正常历史报告、不改默认预算；原有两轮自检的verify继续通过。
- 使用合成临时副本/测试数据，改变耗时并更新summary哈希后仍拒绝，证明拒绝来自新增语义检查。
- 新测试至少包含正常零值、小数值及上述无效类别；完整回归不退化。
- 采用条件：接受有限非负数值规则：`elapsed_ms` 必须是 `int` 或 `float`，但不得是 `bool`，且必须有限、不得小于 0；允许 0 和小数值。
- 修改理由：耗时是成本和运行解释的一部分；布尔值虽是 Python 的 `int` 子类，语义上不是耗时，NaN/Infinity 也不能形成可比较、可汇总的有限测量。
- 自拟检查项：构造 `elapsed_ms=0`、`1.25` 和 `True` 三类临时报告；前两者应通过，后者必须拒绝，并在修改摘要后更新其哈希，以证明失败来自语义检查而不是旧哈希检查。
- 条件冻结日期：2026-10-19（本会话执行前）；冻结版本：R2-duration-v1。
- 冻结内容哈希：以本文件写入后的 SHA-256 为准，后续条件变化须另记理由，不回写本轮冻结条件。

现有函数与候选实现评审（本会话）：`verify` 已有文件完整性、步骤顺序及退出码/状态校验；新增检查放在每步日志关联检查后、状态推导前，读取但不改变原字段。`math.isfinite` 用于排除NaN和Infinity，显式排除`bool`避免Python子类关系把布尔值当耗时。
AI建议取舍：采用非负有限`int`/`float`并允许0和小数；保留历史报告字段和schema版本，不改QNX策略、限流上限或旧manifest；采用更新`summary.json`哈希后的临时反例，驳回只改数据不改哈希的测试方式。

实际执行环境与范围补录（2026-10-19）：用户提供的另一台主机为Windows 26H2 x64、Python 3.11.9、PowerShell 7.6.5；QNX环境登记为QNX SDP 8.0、VMware Workstation 26.0.0和QNX 8.0.0 x86_64 VM。用户报告张润泽与陈卫吉已于2026-10-19交叉验证并签署。现有记录中的R2专门测试由陈卫吉执行；另一台主机的统一自检结果不另计为新的R2实现或QNX运行。


| 实际操作者 | 命令与输入 | 退出码 | 日志/新run_id | 观察及结论 |
| --- | --- | --- | --- | --- |
| 陈卫吉 | `python -m unittest discover -s tests -p test_local_check.py -v` | 0 | 7 tests | 正常0/1.25耗时通过；负数、Infinity、bool且已更新哈希的反例被拒绝 |
| 陈卫吉 | `python -m ipcsec.local_check verify --folder evidence/local-check-runs/20261019T131706Z-eae3eef7` | 0 | 已保存run `20261019T131706Z-eae3eef7` | 历史报告在新增语义检查后仍PASS |
| 陈卫吉 | 临时副本 `build/personal-check-negative-20261019`：将`steps[0].elapsed_ms`设为`-1`并更新`manifest.evidence_hashes.summary.json`；`python scripts/show_local_check.py --folder ...` | 1 | build临时副本，无evidence原件修改 | 报`Invalid elapsed_ms for step: tests`，证明通过完整性层后仍被语义层拒绝；首次PowerShell BOM错误未作为语义结论 |

能解释的三个问题（人工回答记录）：Python的bool是int子类，但语义上不是耗时，所以必须单独排除；只检查非负仍不够，因为字符串、None、NaN和Infinity不能作为可靠的有限测量；更新哈希后的反例先通过文件完整性层，再被elapsed_ms语义层拒绝，证明新增检查确实生效。超大整数修订后按当前条件接受，不额外增加未经批准的上限。

实际接受/修改/驳回的AI建议及理由：本会话按冻结条件实现并记录，AI建议合理，予以采纳。

张润泽验证结论、发现及复验：PASS。实现者确认与验证者签署、时间：陈卫吉-实现者确认 润泽-复核者确认。
