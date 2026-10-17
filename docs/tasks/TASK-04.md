# TASK-04 独立探针与恢复

状态：独立进程与只读OS探针、受控SIGTERM退出及恢复切片已实测；完整故障隔离与阻塞超时路径仍待完成。
关联：ISO-01。
输入与DoR：已授权探针和快照。
范围：完成该纵向切片，不扩大系统或目标。
依赖：前序相关任务通过；主机与原生门分别判断。
DoD及验证证据：超时不误判、完整故障观测与恢复。
负责人：A/B待实名，轮换登记review/roles.md。
停止：授权不足、预算耗尽、连续三次同类关键失败或影响范围超出批准。
当前未知与人工问题：按docs/open-questions.md维护。

证据：review/native-recovery-milestone.md。停止、缺设备与新PID恢复分别观测；不以timeout推断crash，不将受控SIGTERM称为漏洞崩溃。

暂停超时切片未通过，真实注入按连续失败停止规则暂停；Q-ST-01见review/native-stall-issue.md。最新专用gate修复只完成编译与主机验证。

后续更新：用户重新要求继续后，gate检查点版本真实2秒发送侧超时及同PID恢复通过，默认停止/重启回归通过，见review/native-stall-milestone.md。前述停止状态保留为历史；完整系统隔离仍未验收。
