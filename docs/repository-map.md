# 仓库地图

| 入口 | 职责 |
| --- | --- |
| README.md及AGENTS.md | 启动、边界、验证与规则入口 |
| docs/项目工作流.md | 从开题到个人答辩的完整流程 |
| docs/项目适配评估.md | 附件符合项、差距、修正及Ready条件 |
| docs/intent.md及problem-frame.md | 原始目标、Gate和问题边界 |
| docs/specification.md及acceptance-matrix.md | 稳定要求、场景及验证映射 |
| docs/state-model.md及impact-map.md | 状态、影响、兼容与恢复 |
| docs/adr/及tasks/ | 决策、8项任务和质量门 |
| ipcsec/model.py及fuzzer.py | 用例和三类确定性变异 |
| ipcsec/harness.py | 主机目标模型与拒绝静默回退的QNX接口 |
| ipcsec/defense.py及monitor.py | 字段检查、会话窗口和隔离判定 |
| ipcsec/runner.py及metrics.py | 新运行目录、证据索引和指标 |
| ipcsec/evaluator.py及eval/ | 确定性预检、构造校准和LLM设计契约 |
| native/qnx/ | 原生协议草案、接入说明及待实现目录 |
| configs/及tests/ | 试跑参数、边界及回归 |
| evidence/及review/ | 原始事实、解释、校准、角色及签署 |
| release/ | 启动、重置、恢复、已知限制与连续性 |

六类交付映射：Brief对应problem-frame与intent；Design对应spec、ADR与Harness；
eval对应验收和用例；evidence对应运行原始记录；release对应交接；review对应复核及签署。
