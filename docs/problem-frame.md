# 问题框架

2026-10-22。对象为授权自建lab-resmgr-01，输入为有限ECHO应用载荷，输出为应答、错误或网关拒绝及关联记录。问题是能否区分非法输入、策略阻断、目标接收、超时和进程退出，并依据版本化证据交接。

QNX8 x86_64工具链、VM、合法devctl、快照恢复及有限探针已有历史验证，不再列为未解决的起步未知；新接管仍要复核当前可用环境，不假定VM在线或沿用旧IP。

不变量：未授权下一请求不执行；defense拒绝不转发；缺完整观测报告未知；主机模拟不冒充QNX。限制是客户端网关可绕过、session非认证、有限OS探针不能证明完整隔离。需求来源见requirements-analysis；当前行为见specification；未决见open-questions；历史见../review/evidence-index.md。
