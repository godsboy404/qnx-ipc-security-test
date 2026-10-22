# 契约版本与登记迁移

2026-10-22，TASK-09，基线17a4a3776080247ec7e19fe3ab3b05a9b787edd9。旧Spec正文标题为draft0.1，但历史登记ID为ipcsec-spec-draft-0.2；此处按登记ID保留，不改旧字节。

| 版本 | 存放与身份 | 用途 |
| --- | --- | --- |
| 历史0.2 | ipcsec-spec-draft-0.2.md；SHA256 30e09a0d48fe9dfc0948d62d37acc55f81a8ae627f9551997ca24dbb4ec7e271 | 旧登记的逐字节契约快照；旧模型档案保持原样 |
| 历史登记 | review-registry-draft-0.2.json | 原configs/review-registry.json逐字节副本，原路径字符串保留，仅用于解释历史关联 |
| 当前0.3 | ../specification.md；SHA256由../../configs/review-registry.json记录 | project_draft、首轮评审稿；新本地packet绑定此ID及哈希 |

改变内容：重组八条Req、GWT及限制，明确ALLOW阶段计数、baseline范围控制、两后端与历史证据边界；澄清指标，不新增IPC功能或正式批准。

registered_review.py仅支持docs/specification.md及一个当前contract。因此旧绑定保存在快照与旧模型packet中；不声称程序支持两版并行预检。当前登记仅修改contract.id和sha256，release、历史manifest、criteria及source_version保持不变。新packet可核验同一历史档案的有限Claim，不能声称原运行使用0.3或当前源码已原生验证。

旧packet与当前可信登记比对预期不相等，仍不能直接进入当前调用路径；历史模型校准/响应不重新标PASS。旧绑定核验采用快照哈希及原档案，不将旧登记复制到当前路径覆盖新登记。新绑定本轮只做本地预检，模型API调用0，v2真实材料门仍未通过。

核验与保护清单见../../release/first-round-submission.md及其本轮验证记录；不通过修改旧证据实现迁移。
