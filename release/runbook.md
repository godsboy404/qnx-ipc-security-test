# 启动重置恢复与演示

主机模拟需要Python 3.10以上，无第三方依赖。QNX合法链路、变异/防御与授权、受控恢复分别见qnx-vm-runbook.md、native-fuzz-runbook.md、native-recovery-runbook.md。
启动：从项目主目录执行python -m ipcsec demo。验证：python -m unittest discover -s tests -v。
重放：python -m ipcsec replay --case-id CASE-0001；此命令使用配置的固定语料，仅基线单用例，不声称重放有状态频率场景。
重置：每次run自动创建新目标与防御实例、逻辑时钟从0开始，无需删除旧证据。
恢复：模拟新run重置状态；QNX已有快照恢复、目标重启及限定只读探针记录，按专用手册操作并保留新证据。
演示：合法输入，三类变异，无防御模拟故障，有防御NOT_SENT，同一用例重放，隔离INCONCLUSIVE，校准及未知说明。
已知限制：完整系统隔离、正式性能阈值/统计及回复侧取消语义未证明；评价器已接DeepSeek，Schema v2与登记预检见eval/semantic-review-runbook.md；独立真值及隔离审查环境待落实。当前技术证据不等于教师批准、正式课程事件完成或伙伴签署。
伙伴验收：在干净副本执行所有命令，记录Python版本、源身份、结果、恢复及签署；当前待做。
完整步骤见partner-reproduction.md；记录模板见review/partner-reproduction-record.md，演示见classroom-demo.md，提交门见submission-checklist.md。
