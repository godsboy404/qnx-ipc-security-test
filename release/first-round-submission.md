# 第一轮提交验收材料

2026-10-22，提交评审稿，尚未提交Git或由教师验收。代码基线17a4a3776080247ec7e19fe3ab3b05a9b787edd9，本轮主要为文档整理及登记/批准元数据澄清，无IPC功能变更。

## 必交材料

| 产物 | 入口 | 覆盖内容 |
| --- | --- | --- |
| 需求分析 RA-001 v0.1 | [需求分析](../docs/requirements-analysis.md) | 来源/角色、问题、场景、风险、八条需求推导、边界、可行性、验收及未决 |
| 规格说明 draft0.3 | [当前规格](../docs/specification.md) | 输入/输出、八条Req、GWT、适用后端与路径、限制及确认事项 |
| ADR | [决策索引](../docs/adr/README.md) | 可控路径、评价器取舍、限流语义、契约版本管理 |
| 追踪与运行约束 | [验收矩阵](../docs/acceptance-matrix.md)、[Harness](../docs/harness-manifest.md) | Req→实现→检查→Run及版本，Agent与目标运行器边界 |

## 当前版本与核验

旧Spec及登记的逐字节快照见[迁移说明](../docs/contracts/README.md)，新稿仍project_draft。本轮[验证报告](../review/20261022-documentation-baseline.json)、[整理Diff](../review/20261022-documentation-assets-v2/documentation-diff.txt)、[命令记录](../review/20261022-documentation-assets-v2/commands.json)、[文档身份](../review/20261022-documentation-assets-v2/document-source-sha256.json)及[历史保护清单](../review/20261022-documentation-assets-v2/protected-history-sha256.json)已保存。结果为81项主机测试通过、所选归档审计通过、三个criterion本地预检通过、1364个原历史文件保持原哈希；Diff格式及当前文档链接检查通过。

运行主机回归、handoff只读审计、三个criterion本地预检、历史文件哈希保护及Diff检查。本轮模型API调用0、原生运行0、未新增伙伴复现或人工签署。已有v2真实材料门失败保留，新本地预检通过不等于模型语义资格通过。

## 阅读与确认顺序

先需求分析，后规格/ADR，再按验收矩阵抽查八条Req。项目成员检查Diff及计数、批准与指标口径；教师确认首轮材料及具体课程适用要求。独立伙伴按原手册实际执行并生成新记录，最终验收另行完成。

当前待办见[continuity](continuity.md)与[open-questions](../docs/open-questions.md)。文档交付不等待独立互评，但不将其写成已完成。本文材料格式为仓库Markdown，用户未提供额外学校模板，不虚构签章或评分。
