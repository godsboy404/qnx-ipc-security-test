# 架构决策记录索引

2026-10-22首轮提交。ADR描述背景、备选、取舍、后果和验证，状态按实际决定来源区分，不以文档存在代替教师批准。

| ADR | 决策 | 状态与关联 |
| --- | --- | --- |
| [0001](0001-controlled-path.md) | 自建资源管理器及可控客户端路径，分离模拟/原生 | 用户授权实施；课程设计确认仍Proposed；SEC-01/03、IPC-01、ISO-01、REL-01 |
| [0002](0002-evaluator-reasoning-profiles.md) | 评价器推理配置比较后暂不授予正式资格 | 原历史工程记录不修改；NEEDS_MORE_EVIDENCE；OBS-01 |
| [0003](0003-rate-accounting.md) | 只计ALLOW阶段请求，拒绝不延长窗口 | 用户已决定，主机修复；伙伴复核待完成；SEC-04 |
| [0004](0004-contract-versioning.md) | 新契约与历史模型/证据分离 | 本轮工程方案待评审冻结；OBS-01、ISO-01、REL-01 |

需求来源见../requirements-analysis.md，行为见../specification.md，验证见../acceptance-matrix.md。正式E1/E2/E3与最终签署另行记录。
