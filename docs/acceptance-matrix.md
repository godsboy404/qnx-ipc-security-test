# 验收矩阵

2026-10-22。当前评审契约ipcsec-spec-draft-0.3（下表0.3）。历史证据仅用于追踪对应需求，不表示这些Run原先使用0.3，也不代表当前HEAD统一原生实测。所有检查均不需要模型API。H1为主机回归，H2为只读档案审计，H3为本地登记预检，命令见表后。

| Req | 契约/场景 | 实现入口 | 检查/测试 | 证据Run | 结论边界 | 待完成 |
| --- | --- | --- | --- | --- | --- | --- |
| SEC-01 | 0.3/A03 | ipcsec/runner.py；native/qnx/client/lab_fuzzer.c、probes/lab_auth_control.h | H1 test_contracts、test_native_policy；H2 | E07/E08 | 逐请求同步授权24例各8转发16拒绝；非在途撤销或可信身份 | 伙伴复核 |
| IPC-01 | 0.3/P01 | native/qnx/target/lab_resmgr.c、client/lab_client.c | H1 test_native；H2合法链路哈希，原生内容结论见历史记录 | E01 | 历史100+空1+重启100，不代表本轮新执行 | 伙伴当前版本复现 |
| FUZ-01 | 0.3/A01 | ipcsec/fuzzer.py、native.py；native/qnx/client/lab_fuzzer.c | H1 test_contracts、test_native；H2 | E02 | 固定128例、单例重放；未证明漏洞检出或协议全覆盖 | 正式重复Trial |
| SEC-03 | 0.3/P02/N01/N02/A01 | ipcsec/defense.py；native/qnx/include/lab_policy.h、target/lab_resmgr.c | H1 test_contracts、test_native_policy；H2、H3 SEC-03 | E03/E04 | 同语料94例非法阻断且接收记录吻合；客户端路径非系统强制 | 伙伴复核 |
| SEC-04 | 0.3/A02 | ipcsec/defense.py；native/qnx/include/lab_policy.h | H1 test_native_policy、test_change_rehearsal；H2 | E05/E06；../review/findings/INT-F-01-rate-accounting.md | 原生24例验证会话和等待恢复；精确窗口为合成时钟。21例修复为主机对照，不称新增QNX复现 | 独立复核；CH-01未采纳 |
| OBS-01 | 0.3/全部 | ipcsec/runner.py、native.py、registered_review.py、handoff.py；target/lab_resmgr.c | H1 test_handoff、test_review_v2；H2、H3 OBS-01 | E01至E10及各manifest | 本地完整性与语义重算，不证明真实性/签名/独立复现；未由哈希重建历史源文件 | 人工签署及个人引用 |
| ISO-01 | 0.3/U01/R01/R02 | ipcsec/monitor.py、recovery.py、stall.py；native/qnx/probes/ | H1 test_contracts、test_recovery、test_stall；H2、H3 ISO-01 | E09/E10 | 缺证据正确报未知可检查；完整隔离证明未完成。受控信号不是漏洞crash | 完整系统观测、回复侧取消语义不在已证实范围 |
| REL-01 | 0.3/R01/R02及伙伴接管 | native/qnx/probes/lab_recovery.c；release/partner-reproduction.md、native-recovery-runbook.md；ipcsec/handoff.py | H1 test_recovery、test_stall、test_handoff；H2 | E09/E10 | 作者退出重启及同PID恢复已历史实测；伙伴接管仍pending | 伙伴实际新运行及最终签署 |

## 检查入口

H1（主机）：`python -m unittest discover -s tests -v`。表中test_*指tests目录对应模块；不执行VM。

H2（只读历史归档）：`python -m ipcsec.handoff audit`，选择由configs/handoff-evidence.json管理，同时保留历史FAIL/INCOMPLETE；合法链路与不同类型档案的核验强度按审计报告解释，不将所有档案都说成完整重算。

H3（仅本地packet）：`python -m ipcsec.registered_review --release defense-20261017 --criterion SEC-03 --out <新的输出文件>`；OBS-01、ISO-01分别替换criterion，输出路径须尚不存在。只验证登记及有限档案，不调用模型、不提升模型资格、不代替原生运行。

## 历史证据身份

源身份优先使用manifest的source_version；没有该字段时，采用source_hashes映射的排序紧凑JSON SHA256（与semantic_review.identity相同）。它是历史源码映射身份，不是Git提交，也不保证源码可重建。

| ID | Run/manifest | 源身份 | manifest SHA256 |
| --- | --- | --- | --- |
| E01 | [ 20261015T104537Z-afa1f753 ](../evidence/native-runs/20261015T104537Z-afa1f753/manifest.json) | 09207447a23e63e675c542452761a90ad1cb104ee346aebfec0c6cb93311f440 | 3b6cda551e9e3ede3396f33a0a7384f639518abe226e7b3657179c71166572ac |
| E02 | [ 20261017T121606Z-e29291df ](../evidence/native-fuzz-runs/20261017T121606Z-e29291df/manifest.json) | 11b48e1d68d2bef37093dd0381f649598313a73ea535de24ad2f441d5923662e | e816d555867858b37dd87abd65165f7f23fb7a488a64e8fd8a3e0287f4e0ac48 |
| E03 | [ 20261017T122304Z-ad2730f7 ](../evidence/native-fuzz-runs/20261017T122304Z-ad2730f7/manifest.json) | 75049b2ab8894422acbb33225eadc7dca5a078cabaea8086fb197a89e7e4e46e | bdc45c6345a1a895d2fffd6937b23347b12eb408d250ca83b3881c3ef5460b88 |
| E04 | [ 20261017T122327Z-0b2f7718 ](../evidence/native-fuzz-runs/20261017T122327Z-0b2f7718/manifest.json) | 75049b2ab8894422acbb33225eadc7dca5a078cabaea8086fb197a89e7e4e46e | 9b3c14e8c90c3d614e7e0eb5c90398be4a9c9b334b36a0d81d184b58aa73f84b |
| E05 | [ 20261017T122624Z-166ba568 ](../evidence/native-fuzz-runs/20261017T122624Z-166ba568/manifest.json) | bb04ab3199b5e0848666d56608e8e72e8d8be1551cd5e14ee45960a6b19f41e8 | 499c737be0a6836fd515ee01817c0694a98c56208b0a93c5f5590f4078e24271 |
| E06 | [ 20261017T122645Z-89c9b79f ](../evidence/native-fuzz-runs/20261017T122645Z-89c9b79f/manifest.json) | bb04ab3199b5e0848666d56608e8e72e8d8be1551cd5e14ee45960a6b19f41e8 | 0000780cf0663fefd6dd5fc52559f83db8c3936fb6e1c1e88caedc91910b4f1c |
| E07 | [ 20261017T123348Z-63e1b79f ](../evidence/native-fuzz-runs/20261017T123348Z-63e1b79f/manifest.json) | 467edb0af8c520bd0e2ed13baefd25366e5cb5171dc3b417df42e079cb4e944d | bb493197195649caaf6931be3ce02bd90969bdf3d2c7189895fc7cd419cb946f |
| E08 | [ 20261017T123421Z-e4e1c71d ](../evidence/native-fuzz-runs/20261017T123421Z-e4e1c71d/manifest.json) | 467edb0af8c520bd0e2ed13baefd25366e5cb5171dc3b417df42e079cb4e944d | f8bf81b372d33def6d9aa0c41b50b57debd1eb64862eaf54b7f48dffe012dc83 |
| E09 | [ 20261017T130304Z-d6c6072a ](../evidence/native-recovery-runs/20261017T130304Z-d6c6072a/manifest.json) | bf2843a5f8708393fc5f4cd893e4be592e33ca82fbc2778ff7fa296260f974b1 | bd1131ea6ef7e8033048e616ada74e7bbe088de57c35018e527461fa83dcc743 |
| E10 | [ 20261017T130224Z-8ed73897 ](../evidence/native-stall-runs/20261017T130224Z-8ed73897/manifest.json) | bf2843a5f8708393fc5f4cd893e4be592e33ca82fbc2778ff7fa296260f974b1 | 49b5044da9ac19773ea7ab71541225088a02035bc5844f36fe58b28f686542d3 |

本轮文档核验记录见../release/first-round-submission.md；历史技术解释见../review/evidence-index.md。
