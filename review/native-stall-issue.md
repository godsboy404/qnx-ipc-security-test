# 受控暂停超时历史问题与恢复验证

日期：2026-10-17。关联ISO-01、REL-01、OBS-01。问题ID：Q-ST-01。
范围：本轮创建的自建/dev/ipcsec-lab进程；未操作系统服务或第三方目标。

**最新状态**：用户明确要求继续后，专用gate修正版在20261017T130224Z-8ed73897通过真实发送侧2秒超时与同PID恢复验收；停止/重启回归亦通过。见native-stall-milestone.md。下文保留此前停止时的事实和判断，不代表当前仍未执行修正版，也不将旧失败改为通过。

## 真实结果

| 运行ID | 观察及处置 |
| --- | --- |
| 20261017T124634Z-34573af9 | 监督进程在目标暂停后查询设备路径，自身被阻塞；45秒宿主截止触发。根据本轮日志确认的PID 12980251发送SIGCONT后恢复清理。原始目录保留，后续日志另存native-stall-incidents/同ID |
| 20261017T124922Z-231db1b3 | 移除暂停设备查询并增加6秒SIGALRM；暂停被观测，结果保存未完成，兜底恢复并回收所有实际启动子进程，FAIL |
| 20261017T125108Z-2e129a1a | 预先建立结果和追踪句柄；未形成完整超时结果，6秒兜底恢复并清理，FAIL |
| 20261017T125343Z-5d4bca62 | 首版接收前检查点仍存在触发竞态；专用检查点请求前可能有设备查询的收尾消息，暂停早于预期。6秒兜底恢复并清理，FAIL |

原始证据位于evidence/native-stall-runs/各目录，均未覆盖或补写成成功。后3轮stall-cleanup.json均显示pause_watchdog_triggered=true、complete=false、all_owned_children_reaped=true、device_present=false。失败证据缺少after.jsonl或完整结果，旧运行没有summary时不伪造补齐。单元测试通过不能替代这些失败事实。

## 已确认与待验证的判断

已确认：暂停期间对目标设备执行access可能阻塞监控；现已移除，设备可见性记录null。新6秒信号兜底已在后3轮实际触发并完成恢复清理。
QNX官方说明，服务器已接收消息且采用_NTO_CHF_UNBLOCK时，客户端解除阻塞可能依赖服务器处理；所以单纯SIGSTOP并不能保证发送侧2秒退出。现有表现与此语义一致，但未用内核跟踪完成排他性根因证明。
本机libc反汇编显示devctl调用MsgSendv_r，ELF带BIND_NOW；没有证据支持把失败归因于首次延迟绑定。
首版“循环末尾发现标记就暂停”仍可能被前一个设备查询的收尾处理触发。离线修复为：只有显式启用--controlled-pause且收到合法gate ECHO时才设置检查点，完成该次回复后、下一次dispatch_block之前暂停。其他stat/open/close不能触发。客户端、接收审计和主机oracle均区分gate与ping。

## 停止时的交付状态（历史）

离线修正版严格编译通过；37项主机回归通过，其中暂停场景合成fixture验证了超时码与时序、同PID、独立探针覆盖、额外延迟交付拒绝、专用gate身份、兜底触发不得PASS及缺证据不推断crash。
**最新gate修正版尚未在QNX执行；真实2秒超时、同PID恢复应答均未验收。** 目标暂停不是crash，隔离结论仍为INCONCLUSIVE。
按AGENTS.md及harness-manifest的连续三次同类关键失败停止规则，已停止继续真实注入，记录本人工问题。后续应先复核专用gate检查点与日志顺序，再由用户重新指示继续；不能通过降低超时规格、忽略兜底或删除失败证据来完成验收。

参考：[TimerTimeout](https://qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/t/timertimeout.html)、[waitpid](https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/w/waitpid.html)。
