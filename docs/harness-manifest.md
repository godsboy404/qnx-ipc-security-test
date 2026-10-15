# Harness清单

Runtime：当前Python单进程模拟，单槽、确定性语料；无网络、无shell调用、无生产系统访问。
新增原生合法路径：用户授权的新建QNX 8.0 VM、自建/dev/ipcsec-lab、项目专用SSH密钥；只运行合法ECHO及自建服务重启。
原生每次请求2秒SEND/REPLY超时，主机执行截止45秒；阻塞场景本轮未测试。VM使用已有VMnet8，移除Guest默认路由。
Project：本目录AGENTS、docs、configs、tests、eval、evidence、review和release。
验证命令：README四条命令均需可运行；QNX不提供伪可执行命令，见native/qnx/README.md待实现项。
预算：每场景100例、4场景，总400例；真实测试时间与API成本待试跑批准。
允许：本仓库读写、主机模拟、回归。禁止：真实系统扫描、敏感数据、修改旧证据。
需批准：教师Intent Gate、故障注入、变更CH-01和发布。用户已明确授权创建本机实验VM、部署Hello与自建合法IPC；不据此声称教师审批完成。
Stop：未知目标、原生后端误调用、同类关键失败三次、预算耗尽。
恢复：模拟新实例新run；原生依赖快照和外部watchdog，尚未完成。
上下文：全局入口仅地图与规则；任务按需读取Spec、ADR、代码和测试；日志限必要字段。
权威：批准的课程契约优先于目标README；运行事实在evidence；教师批准和签署在review。
配置评估：每改规则/限流/权限，重跑相同语料、窗口边界和校准样例，报告结果及成本变化。
