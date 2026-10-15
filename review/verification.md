# 初始工程验证记录

日期：2026-10-15。执行来源：本机AI工具调用，非伙伴独立复现。Python 3.12.14，Windows。

## 已执行

- `python -m unittest discover -s tests -v`：9项通过。
- `python scripts/check_environment.py`：当前终端qcc、QNX_HOST和QNX_TARGET均未发现。
- `python -m ipcsec demo`：4场景各100条模拟用例，共400条。
- `python -m ipcsec replay --case-id CASE-0001`：1条模拟单例重放。
- `python -m ipcsec calibrate`：K1至K6确定性fixture与预期一致；不包含模型语义校准。
- `python scripts/verify_evidence.py`：5个运行目录的哈希、身份、条数及拒绝不转发检查通过。

所有运行在evidence/runs/独立目录，manifest保留当时源文件哈希。每次运行的源身份覆盖代码、配置、规格等，
本记录属于review层，不参与源身份计算。后续编辑相关文件须产生新运行，不回写旧结果。

## 实际覆盖

合法0至64字节、声明与实际长度冲突、非法offset、会话窗口边界与会话独立、语料可重复、
三类变异、未登记目标拒绝、原生接口不静默模拟回退、缺探针时不判隔离成功、零分母和错版本评价。
集成检查另外核查所有BLOCK/RATE_LIMIT结果为NOT_SENT。

## 不支持的结论

未运行QNX原生构建、真实IPC、真实崩溃、系统探针、隔离恢复或真实性能实验。
模拟Target的SIMULATED_FAULT是模型事件，无宿主进程崩溃。EXP-04是固定池重排机制探索；
当前防御阻断全部生成的非法输入时，没有模拟故障反馈可触发优先级调整，不据此宣称对抗收益。
K1至K6为构造fixture，不证明LLM抗注入能力或总体准确率。

独立复核、人工签署及教师正式审批均为pending。

## 文档交付

正式工作流为docs/项目工作流.md，评估和结构为相邻Markdown文件。
Word草稿留在.qa内部；打包渲染器报告缺少soffice.exe，未作为可交付Word发布。
