# 仓库地图

| 入口 | 职责 |
| --- | --- |
| README.md、AGENTS.md | 启动、规则与文档入口 |
| release/first-round-submission.md | 首轮需求分析、规格、ADR及核验交付索引 |
| docs/requirements-analysis.md、intent.md、problem-frame.md | 需求来源、场景、边界及取舍 |
| docs/specification.md、acceptance-matrix.md | 当前Req/GWT与版本化追踪 |
| docs/contracts/ | 旧契约/登记快照及显式迁移记录 |
| docs/harness-manifest.md、open-questions.md | 两类Harness、权威、假设、可见性及缺口 |
| docs/adr/、tasks/、plan.md | 架构决定、任务及依赖 |
| ipcsec/model.py、fuzzer.py、runner.py、defense.py、monitor.py、metrics.py | 主机用例、变异、执行、策略、未知判断及旧指标计算 |
| ipcsec/native.py、recovery.py、stall.py、simulation_evidence.py | 原生归档与恢复/暂停、模拟证据核验 |
| ipcsec/registered_review.py、review_contract_v2.py、semantic_review.py、model_calibration.py、claim_audit.py | 登记预检、评价契约、有限模型调用、校准与本地断言 |
| ipcsec/handoff.py、local_check.py | 交接审计/打包与作者自检 |
| native/qnx/include、target、client、probes | devctl协议/策略、资源管理器、客户端/Fuzzer、独立监控/恢复 |
| native/qnx/transport | 批处理桥接说明；Python逐请求QnxTransport仍未实现 |
| configs/、tests/、scripts/ | 范围/预算/登记、主机回归、构建部署与检查 |
| evidence/、review/ | 原始运行及历史解释/签署，禁止改写 |
| release/ | 演示、运行手册、伙伴接管和当前状态 |

当前状态唯一摘要见release/continuity.md；历史技术索引见review/evidence-index.md。状态图与影响分析在docs/state-model.md、impact-map.md；课程映射见项目工作流.md和项目适配评估.md。
