# TASK-04 独立探针与恢复

状态：独立进程与只读OS探针、受控SIGTERM重启、专用gate发送侧2秒超时及同PID恢复均已实测。完整系统隔离与回复侧完整取消语义仍未知。失败过程见review/native-stall-issue.md。
关联：ISO-01。
输入与DoR：已授权探针和快照。
范围：完成该纵向切片，不扩大系统或目标。
依赖：前序相关任务通过；主机与原生门分别判断。
DoD及验证证据：超时不误判、完整故障观测与恢复。
项目联系人：张润泽、陈卫吉；个人轮换R1为张润泽实现/陈卫吉验证，R2反向，见review/roles.md。此为当前成员及实际两轮记录，不追认此前各技术切片为个人独立实现。独立互评成员邓一帆，执行状态另行记录。
停止：授权不足、预算耗尽、连续三次同类关键失败或影响范围超出批准。
当前未知与人工问题：按docs/open-questions.md维护。

证据：review/native-recovery-milestone.md。停止、缺设备与新PID恢复分别观测；不以timeout推断crash，不将受控SIGTERM称为漏洞崩溃。

专用gate发送侧2秒超时及同PID恢复已有历史通过，见review/native-stall-milestone.md。后续依赖为伙伴实际复核；完整系统隔离和回复侧完整取消语义仍未知。
