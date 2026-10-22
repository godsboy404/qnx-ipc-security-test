# INTENT-001 当前项目意图

2026-10-22整理；原始立项2026-10-15。问题：对可控QNX资源管理器接口开展可重复测试，验证客户端防御与限定故障影响，形成可复核证据和伙伴交接材料。

对象：本机授权QNX8 x86_64 VM内自建lab-resmgr-01（/dev/ipcsec-lab）。参与者、需求推导见[需求分析](requirements-analysis.md)，行为见[规格](specification.md)。

教师已同意选题，依据为用户2026-10-19转述，见../review/teacher-approval-20261019.md；教师姓名和原始批准时间不代填。规格仍为项目草案，正式E1/E2/E3与最终课程验收待实际记录。

现有授权覆盖同一自建目标的合法IPC、有界变异、客户端网关、私有逐请求授权、独立监控及本轮自建进程SIGTERM退出/重启、SIGSTOP/SIGCONT暂停恢复。只读OS探针限uname与/proc状态检查。原生服务、系统服务攻击、漏洞崩溃注入和第三方目标不得混淆；本轮文档整理不执行原生实验。

非目标：透明拦截全系统MsgSend、生产部署、系统服务/第三方目标测试、可信会话认证、完整系统隔离保证。扩大范围需明确授权和可恢复设计。

历史授权过程与技术演进分别见../review/native-milestone.md、native-fuzz-milestone.md、native-defense-milestone.md、native-authorization-milestone.md、native-recovery-milestone.md、native-stall-issue.md和native-stall-milestone.md。旧失败保留，不再混入当前规则正文。
