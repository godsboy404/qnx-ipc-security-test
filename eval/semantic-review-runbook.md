# 评价器运行手册（Schema v2）

更新：2026-10-19。关联OBS-01、SEC-03、ISO-01。旧Schema v1只保留历史离线核验；新实时CLI使用Schema v2。schema版本与校准批次版本是两回事。

## 字段与权威

- backend：fixture / simulation / qnx_native / host，表示运行环境。
- evidence_source：target_runner / peer_runner / teacher_runner / static_inspection / fixture_demo / target_claim，表示来源。
- verification_level：CLAIM_ONLY / STATIC / OBSERVED / REPRODUCED，表示输入证据强度；输出evidence_level使用同一强度集合，无引用时为NONE。
- 输出evidence_sources和backends必须与引用精确对应；混合引用采用最弱层级，不能将本机重算称为伙伴复现。
- contract.status当前为project_draft。未配置可信教师N/A批准，真实材料禁止NOT_APPLICABLE。K6的synthetic-na-only只用于构造校准，不是实际教师批准。

完整强制校验在ipcsec/review_contract_v2.py。模型无Shell、目标代码执行或补测工具；输出不得给成绩或替人签署。未配置完整系统探针验证器，ISO-01不能PASS。

## 本地登记预检（不联网）

configs/review-registry.json只登记一个历史防御run及三个有限Claim，固定规格、原始manifest及源身份。ipcsec.registered_review在读取有限片段前校验大小、路径、链接、规格/manifest哈希，并从原始请求与接收记录重算。没有登记的release/criterion拒绝。规格或档案变更必须先人工复核再更新登记，不能自动接受新哈希。

```powershell
New-Item -ItemType Directory -Force build | Out-Null
python -m ipcsec.registered_review --release defense-20261017 --criterion OBS-01 --out build/review-packet.json
```

这产生派生审查输入，不运行目标代码、不访问VM。真实材料发出前会再次按受信登记重建并比对packet，编辑摘要即便重算excerpt哈希也不能绕过。登记是项目所有者维护的本地信任根，不是密码学签名或教师注册表。

## 受控模型调用

DeepSeek读取本机DEEPSEEK_API_KEY，固定发送到https://api.deepseek.com/responses。新Schema v2候选路由显式设置OBS-01为reasoning.effort=high，其余为none，max_output_tokens=1500；网络截止45秒。官方配置依据：https://api-docs.deepseek.com/guides/thinking_mode/ 。旧默认推理及3000-token诊断失败均保留，不隐藏。

```powershell
python -m ipcsec.semantic_review --provider deepseek --model deepseek-flash --packet build/review-packet.json --run-dir build/model-review/new-dedicated-run
```

调用会产生费用，数据发送须在既有明确授权范围内。此前用户许可仅覆盖构造样例与已列明的三份自建QNX有限摘要，不覆盖其他项目或敏感数据。DeepSeek返回store=false不等于数据留存政策保证。

通用单packet入口最多10次/专用目录，换目录不构成账户级预算；正式批次使用下述一次性执行器。当前路由构造样例通过，但新格式真实材料门未通过，只能作为待人工核查草稿，不进入正式E3。过程见review/20261019-evaluator-and-handoff.md。

## 冻结校准及真实材料批次

```powershell
# 新目录；只准备，不联网
python -m ipcsec.model_calibration prepare --folder evidence/model-review-runs/new-fixture-snapshot
python scripts/Prepare-ModelEvidence.py --folder evidence/model-review-runs/new-registered-snapshot

# 人工核对输入、授权及预算后，显式执行选定批次
python -m ipcsec.model_calibration execute --folder evidence/model-review-runs/new-fixture-snapshot
python -m ipcsec.model_calibration verify --folder evidence/model-review-runs/new-fixture-snapshot
```

每快照1—10条，每条只调用一次，独占started标记阻止并发或隐式续跑；连续3项失败停止。保留答案、请求、原始响应、usage、timing、拒收类型及源码；真实材料另冻结登记与规格副本。答案与人工保留变体不得进模型输入。

verify从原始响应重算并核验完整文件集；旧Schema v1原始结果按原规则读取，不迁移或重写。Refusal、incomplete、引用/来源/层级不符全部拒收。timing测量网络与输出验证，不含本地预检；历史记录没有的时间不得倒填。

工程样例及预期答案由AI编写，独立人工真值、伙伴校准、OS级隔离工作区和最终签署仍待落实。不要在有宿主Secret的目录执行陌生被评仓库脚本；这个只读预检入口不提供目标执行能力。正式E2/E3仍按教师和伙伴流程执行。
