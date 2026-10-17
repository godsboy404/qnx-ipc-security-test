# 课程交付清单与当前缺口

状态：本地交接草稿。技术证据核验通过不等于课程Release Gate或成绩通过。

| 交付域 | 当前资产 | 当前判断及责任 |
| --- | --- | --- |
| Brief/Intent | docs/intent.md、问题框定、项目适配评估 | 草案具备，教师选题接受待人工记录 |
| Design/Spec/Plan | 规格、Req/GWT矩阵、任务、ADR、状态图、双层Harness清单 | 已建设，人工确认版本及课程适用范围 |
| 原生实现 | 自建服务、合法客户端、有界Fuzzer、客户端网关、会话限流、监控及恢复 | 限定功能有实测；不等于全系统防护 |
| E1实验 | 同语料防御比较、原始请求/接收审计、授权与恢复数据 | 有技术数据，正式E1取舍及成本/Trial要求需教师确认 |
| E2 Change | review/CH-01.md、候选配置、三组22例证据 | 候选模拟与回滚通过；Proposed，未批准或正式采用，原生仍为10 |
| E3审查 | release/e3-review-guide.md、内部INT-F-01及21例修复回归 | 用户选定放行计数，主机修复通过；独立伙伴复核与正式E3待执行 |
| 评价Agent | 确定性基线、受限Responses适配器、冻结校准及原始响应 | DeepSeek构造校准v2为10/10，真实有限材料v2为3/3；旧失败保留，独立人工真值与伙伴校准仍待做 |
| 证据与版本 | 原始manifest、比较报告、只读核验、当前源码快照 | 原始哈希可核验；不同历史源码不由哈希重建，伙伴用当前源码产生新证据 |
| 交接恢复 | VM/变异/恢复手册、伙伴步骤与记录模板 | 原作者恢复有实测，伙伴干净环境执行及签署待做 |
| 个人能力 | review/roles.md、AI披露、个人解释问题 | 实名、真实轮换与个人独立实现/验证证据待填 |
| 演示与提交 | classroom-demo.md、evidence-index.md、本地ZIP | 已准备草稿，发布和最终签署待人工决定 |

## 交接包构建与复核

```powershell
python -m ipcsec.handoff audit
python -m ipcsec.handoff package
python -m ipcsec.handoff verify-bundle --archive <生成的ZIP路径>
```

输出在build/handoff/唯一目录：ZIP、handoff-audit.json、source-snapshot.json、SHA256SUMS.txt。包内PACKAGE-MANIFEST.json记录每个文件哈希；不含SDK、VM磁盘、编译二进制、SSH私钥、build和.git。包保留历史失败及未完成记录，不作为公开发布操作。
审计选择7项历史证据和3组比较，另外检查历史manifest及事件恢复日志完整性。历史FAIL/INCOMPLETE保留并单列；它们不会因为所选修复版本通过而被改写。课程状态始终PENDING、伙伴复现false，直到有真实人工证据。
交接包不包含所有历史版本源码/二进制，因此不能声称包内当前源码与全部历史实验完全同版。SOURCE-SNAPSHOT是当前材料的冻结身份；历史manifest另指当时版本。

## 人工收尾顺序

1. 教师确认选题、E1范围与需要完成的E2/E3及评价Agent要求；批准或收缩范围必须记录，不能由AI预填N/A。
2. 填写真实成员与独立结对组，按partner-reproduction.md独立执行并产生新证据。
3. 完成正式Change、Finding/回应与评价器校准；当前提案保持Proposed，未执行项保持未完成。
4. 每人补实际轮换、个人修改/验证记录、AI使用及能解释的路径，签署限定结论。
5. 冻结最终提交版本后重新打包、核验、排练；由人决定最终提交或发布。
