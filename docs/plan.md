# 实施计划

执行顺序和周次见项目工作流第3节。任务卡TASK-01至08为入口，任务之间用质量门控制。
当前里程碑：QNX合法路径、有界原生Fuzzer、独立进程监控、客户端网关和会话限流对照均已实测。最新见review/native-defense-milestone.md。
动态撤权与授权异常关闭路径已实测，见review/native-authorization-milestone.md。
受控SIGTERM退出、新PID恢复及独立只读OS探针已实测，见review/native-recovery-milestone.md。
下一里程碑：阻塞超时与更完整的故障观测；伙伴复现及课程交付。当前不宣称全系统故障隔离。

阻塞超时状态更新：连续三轮暂停验收未完成，已停止真实注入并登记Q-ST-01。专用gate检查点修复已编译和主机校验，尚待QNX验收，见review/native-stall-issue.md。

最新里程碑：用户重新指示后，真实发送侧2秒超时与同PID恢复通过，停止/重启回归通过，见review/native-stall-milestone.md。下一步优先整理课堂演示和证据索引、伙伴复现，教师Gate及人工签署不由AI代填；完整系统隔离保持未知。
并行允许：规格、语料和文档准备；原生畸形消息发送依赖合法路径、授权、watchdog、恢复全部完成。
每轮两人交换实现与验证。新依赖、原生权限和真实执行另行记录批准，不由脚手架默认启用。
