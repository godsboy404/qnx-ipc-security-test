# QNX 原生接入状态

状态：尚未实现，禁止将主机模拟验收替换为QNX验收。
include/lab_protocol.h仅定义应用载荷草案，不能直接作为资源管理器系统消息头。

建议先建立一个自建教学resource manager与一个合法client，采用devctl自定义命令建立最小往返。
确定消息封装、大小与handler后，再增加受控畸形载荷测试；若必须直接MsgSend，应先按官方文档完成消息分发与连接契约。
不要把任意裸结构直接发送给系统资源管理器。

下一步落实：
1. 记录目标架构、qcc版本、QNX 8.0镜像、许可证与教师授权、快照恢复。
2. target/ 实现仅绑定自建实验设备的resource manager。
3. client/ 实现合法请求及返回验证；记录真实发送字节与声明字段。
4. transport/ 实现超时与错误分类，核查TimerTimeout及channel unblock行为，并配置外部watchdog。
5. probes/ 由独立进程采集目标退出/信号、客户端、peer、已批准服务与系统心跳及恢复时间。
6. 将native runner结果导入证据结构，先通过100次合法往返，再开放受控变异。

参考链接见docs/references.md。没有可用工具链时不生成伪编译成功记录。
