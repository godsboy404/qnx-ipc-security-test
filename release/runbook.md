# 启动重置恢复与演示

主机模拟需要Python 3.10以上，无第三方依赖。另已完成QNX真实合法链路，操作见qnx-vm-runbook.md。
启动：从项目主目录执行python -m ipcsec demo。验证：python -m unittest discover -s tests -v。
重放：python -m ipcsec replay --case-id CASE-0001；此命令使用配置的固定语料，仅基线单用例，不声称重放有状态频率场景。
重置：每次run自动创建新目标与防御实例、逻辑时钟从0开始，无需删除旧证据。
恢复：终止本次模拟命令后重新运行；不要删旧日志。QNX恢复待快照、目标重启与探针落地。
演示：合法输入，三类变异，无防御模拟故障，有防御NOT_SENT，同一用例重放，隔离INCONCLUSIVE，校准及未知说明。
已知限制：虽有QNX构建、合法IPC和服务重启证据，尚无原生Fuzzer、独立进程隔离及正式性能对照数据；评价器无LLM接入。
伙伴验收：在干净副本执行所有命令，记录Python版本、源身份、结果、恢复及签署；当前待做。
