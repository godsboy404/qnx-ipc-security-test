# 目录职责

lab_monitor.c通过posix_spawn和waitpid监督自己创建的target、worker、peer，独立记录采样与心跳，并以专用子进程校准退出码7和SIGTERM观测。不会将timeout解释为crash。系统服务探针和故障隔离未实现，隔离结论为INCONCLUSIVE。退出时仅回收自己的子进程。

lab_auth_control.h在authorization专用场景中执行授权计划；只原子替换或移除本轮目录的实验授权文件，读回并记录事件后确认客户端下一请求。该控制器与被测客户端是独立进程，详见review/native-authorization-milestone.md。

lab_recovery.c运行独立的受控停止/重启实验：监督进程、两代目标、独立只读OS探针、正常/停机/恢复三个阶段客户端。探针只执行uname和stat(/proc)；目标由监督进程主动SIGTERM停止，并明确记录退出信号、缺设备窗口和新PID。运行见release/native-recovery-runbook.md，不称为漏洞崩溃或全局隔离证明。
