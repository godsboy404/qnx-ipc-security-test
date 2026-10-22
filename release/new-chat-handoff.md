# 新聊天接续说明

更新2026-10-22。仓库D:/Users/Downloads/QNXsec/qnx-ipc-security-test。先读AGENTS及规定基础文档，再读continuity、first-round-submission和TASK-09；摘要不是实时状态，开工核对Git与最新用户消息，不擅自commit/push/reset。

本轮已整理首轮需求分析、当前规格、ADR、验收矩阵与入口。基线17a4a37及未提交文档差异，最新核验身份见首轮索引；不能把文档日期当新提交或原生同版通过。

范围：本机授权QNX VM内自建/dev/ipcsec-lab，已有合法IPC、有界变异、客户端网关、会话限流、动态授权及受控恢复历史。默认10，候选5未采用；网关可绕过，session非认证；timeout不是crash；完整隔离未知。主机模拟与原生分开。

旧登记0.2及Spec逐字节快照在docs/contracts；当前0.3是项目草案，新登记显式绑定，仅本地预检。预检路径固定，旧packet不自动符合新登记；旧模型档案不得改写。v2真实材料门未过，LLM只草稿，禁止打印密钥或擅自外发完整日志。

组内张润泽、陈卫吉两轮由用户报告完成并签署，日志及版本引用待收尾；独立伙伴邓一帆尚无实际复现记录。教师已同意选题，不等于规格逐项确认、正式E1/E2/E3或最终验收。当前待办以continuity及open-questions为准。

环境历史：Windows/PowerShell、Python3.11、QNX SDP8、VMware和QNX8 x86_64；重新核对可用性，不假定VM在线或沿用旧IP。命令见AGENTS。原生操作按release手册，本轮不运行；当前主机回归和归档核验均不称伙伴复现。
