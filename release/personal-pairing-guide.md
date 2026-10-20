# 张润泽与陈卫吉：两轮个人实现与交叉验证

关联：REL-01、OBS-01。准备日期2026-10-19；任务设计由AI辅助，后续用户报告两轮实施、交叉验证及签署已完成，代码复查81项通过，见review/20261019-personal-rounds-recheck.md。修改身份及日志引用待收尾。以下保留任务执行方法，不表示仍未实施。邓一帆的独立互评另行跟踪。

张润泽报告的自检 `20261019T131706Z-eae3eef7` 已只读重验通过，作为开始前的工程检查点；不将其倒填为本次任务的实现或同伴验证。

## 第一轮：张润泽实现，陈卫吉定义验收并验证

建议修改：新增 `scripts/show_local_check.py`，把一次统一自检报告显示成便于课堂阅读的摘要。只处理已保存的自检结果，不发API、不启动VM、不重跑实验。

陈卫吉先读 `review/personal-rounds/R1-summary.md`，自行修改/采用条件并写出理由、日期及一个自己提出的检查项，然后冻结这份条件。冻结后张润泽才开始实现；后续条件变化需另记理由。

实现提示（不是完整答案）：参照scripts内现有Python入口配置仓库import路径；用argparse接收必填--folder；先调用 `ipcsec.local_check.verify`，再调用 `verify_generated` 核对关联证据；把返回报告显示成人能读懂的表格。预期验证错误由CLI给出简短诊断和非零退出码，不能把损坏证据当PASS。

允许AI辅助：解释现有函数、评审本人候选代码、帮助诊断错误；记录采用/修改/驳回的建议。若由AI生成候选代码，明确写AI生成范围及本人实际修改、验证和理解的部分，不记作独立手写。

建议命令（脚本由本人实现后才可运行）：

```powershell
python scripts/show_local_check.py --folder evidence/local-check-runs/20261019T131706Z-eae3eef7
python scripts/show_local_check.py --help
python scripts/show_local_check.py --folder build/nonexistent-personal-check
```

陈卫吉实际核验正常输出、异常退出码和一个自拟案例；把命令、输出、$LASTEXITCODE及观察保存到自己的记录。负例在build临时副本操作，不改evidence原件。摘要中的PASS仅指已有自检，不能升级课程Gate或独立性。

## 第二轮：陈卫吉实现，张润泽定义验收并验证

建议修改：给 `ipcsec/local_check.py` 的 `verify` 增加步骤耗时字段的有效性检查。目前该函数核对退出码、状态及日志，却不约束elapsed_ms的数值域。负数、布尔值或非有限数值会影响成本记录解释。

张润泽先填写 `review/personal-rounds/R2-duration.md` 并冻结条件；陈卫吉再实现。原有历史证据和输出字段不变，只增加读取检查；正常历史报告应仍可核验。

陈卫吉需要自己补有意义的反例检查：从临时测试数据构造错误elapsed_ms，同时更新摘要文件哈希，确认即使通过文件一致性层仍被语义检查拒绝。可以参考tests/test_local_check.py的已有构造；不能只改数据而不更新哈希，否则测到的只是旧哈希检查。

建议执行：

```powershell
python -m unittest discover -s tests -p test_local_check.py -v
python -m ipcsec.local_check verify --folder evidence/local-check-runs/20261019T131706Z-eae3eef7
python -m ipcsec.local_check run
```

这里的改动不改变模型Schema v2，不修改QNX策略或限流上限，不扩大实验范围。不能通过改旧manifest、删测试或更改现有结果解决失败。

## 每轮如何保存证据

开始前的相关原文件副本和哈希见 `review/personal-rounds/baseline/`，是AI准备的起点快照，不是本人贡献。若开工前相关文件再次变化，由执行者另存新基线。

每轮记录：条件提出/采用者、实现者、实际日期、起止时间、受影响文件、修改前后哈希或本人Commit、新run_id、同伴命令与退出码、一个问题及处理、AI建议取舍、验收结论和签署。没有测量的时间写未知。

建议各人在自己实际操作时使用PowerShell `Start-Transcript -Path <新的日志路径>` 和 `Stop-Transcript` 保存命令与输出，再把路径填入任务卡。原始日志归属于实际操作者，不把本会话自动执行输出换名为学生独立操作。

最后更新review/roles.md中的实际轮次表。Git提交只包含自己确认的文件；工作树已有多轮未提交改动，不要把全部既有工程归为这次个人贡献。可以用 `git diff -- <本轮文件>` 检查，未提交的新文件还需单独阅读。
