# R1：自检摘要展示

Req：REL-01、OBS-01。计划实现者张润泽，验收条件制定与验证者陈卫吉。状态：COMPLETED_REPORTED；AI复核通过，人工签署由用户报告已完成，原始签名附件未入库。

以下为AI提出的候选条件，请陈卫吉先审定并改写/补充，再交张润泽实现：

- 给定已核验的报告，执行新脚本--folder后，显示run_id、总体状态、每步名称/状态/耗时及实际步骤数量，退出码0。
- 显示host self-check、非新QNX运行、非独立伙伴复现及课程Gate PENDING，避免把技术PASS解释为课程通过。
- 缺参数、路径不存在、日志哈希损坏或关联证据缺失时，提供可理解诊断并返回非零退出码，不输出通过结论。
- 只读输入；运行前后被检查文件的哈希不变。新脚本不含API/SSH/VM执行调用。
- 采用条件：保留以上候选条件，并补充要求摘要脚本在显示前完成 `verify` 和 `verify_generated`；任一核验异常都必须给出简短诊断并以非零退出，不能显示总体 PASS。
- 修改理由：摘要工具的职责是解释已核验结果，不是重新解释或升级证据；先完成语义和关联证据核验可避免损坏报告被渲染成可信结论。
- 自拟检查项：摘要中的步骤数量、步骤顺序和每步状态必须与已核验报告一致；摘要不得自行推导新的课程验收或独立性结论。
- 条件冻结日期：2026-10-19（本会话执行前）；冻结版本：R1-summary-v1。
- 冻结内容哈希：以本文件写入后的 SHA-256 为准，后续条件变化须另记理由，不回写本轮冻结条件。

现有函数与候选实现评审（本会话）：`ipcsec.local_check.verify` 先核对自检目录成员哈希、报告步骤顺序、退出码/状态和权限范围；`verify_generated` 再按报告中的关联路径核对生成物的manifest及语义内容。候选摘要脚本只读调用这两个函数，不调用`run`、API、SSH或VM；采用表格显示而非直接信任`summary.json`中的PASS。
AI建议取舍：采用“先验证后显示”、失败简诊断/非零退出、保留课程Gate和证据范围；将候选的“独立伙伴复现”改成明确的`peer reproduced: no`，因为本地报告不能证明伙伴执行；驳回任何把摘要PASS写成课程通过的表述。


实际执行环境与范围补录（2026-10-19）：张润泽在另一台Windows 26H2 x64主机（Python 3.11.9、PowerShell 7.6.5）执行已保存自检的`run`与`verify`，运行ID为`20261019T131706Z-eae3eef7`，约21:17（北京时间）。本次未修改源码；QNX SDP 8.0、VMware Workstation 26.0.0和QNX 8.0.0 x86_64 VM为环境登记，不代表本次产生了新QNX运行。入口命令的`$LASTEXITCODE`未单独保存，不能补写具体数值。用户报告张润泽与陈卫吉已于2026-10-19交叉验证并签署。

| 实际操作者 | 命令与输入 | 退出码 | 日志/运行ID | 观察及结论 |
| --- | --- | --- | --- | --- |
| 张润泽 | `python scripts/show_local_check.py --help` | 0 | 本地命令输出 | 帮助显示必填`--folder`，未执行实验 |
| 张润泽 | `python scripts/show_local_check.py --folder evidence/local-check-runs/20261019T131706Z-eae3eef7` | 0 | 已保存run `20261019T131706Z-eae3eef7` | 8/8步骤PASS；范围为主机自检和历史归档，Gate仍PENDING |
| 张润泽 | `python scripts/show_local_check.py --folder build/nonexistent-personal-check` | 1 | 无新run | 给出manifest不存在诊断，未显示PASS |
| 张润泽 | `python -m ipcsec.local_check run` | 0 | 新run `20261019T133034Z-69f9f883` | 统一自检PASS；不证明伙伴复现或课程验收 |
| 张润泽 | `python -m ipcsec.local_check run`; `python -m ipcsec.local_check verify --folder ...\evidence\local-check-runs\20261019T131706Z-eae3eef7` | 入口退出码未单独保存；报告内8个子步骤均通过且未超时 | `20261019T131706Z-eae3eef7` | 主机自检和历史证据重验完成；无新QNX实测、无模型API调用 |

能解释的三个问题（人工回答记录）：先验证再显示，是为了防止损坏或被篡改的报告先被渲染成可信摘要；不能直接读summary中的PASS，因为manifest哈希、步骤一致性和关联生成证据也必须通过；摘要保留证据范围，是为了明确主机自检不等于QNX实测、伙伴复现或课程验收。AI建议采用先验证后显示和中性范围说明，未采用把PASS升级为课程结论的建议。

实际接受/修改/驳回的AI建议及理由：本会话按冻结条件实现并记录，AI建议合理，予以采纳。

陈卫吉验证结论、发现及复验：PASS。实现者确认与验证者签署、时间：张润泽-实现者确认 陈卫吉复核者确认。
