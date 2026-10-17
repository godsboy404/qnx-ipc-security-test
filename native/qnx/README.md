# QNX 原生接入状态

状态：合法IPC、有界原生模糊测试及独立进程监控均已在新建QNX 8.0 x86_64虚拟机验证。最新变异证据见review/native-fuzz-milestone.md，操作见release/native-fuzz-runbook.md。
原生客户端网关与会话限流对照也已实测，最新见review/native-defense-milestone.md。
早期工具链检查为历史记录；最新运行证据见review/native-milestone.md及evidence/native-runs/。
include/lab_protocol.h定义devctl应用载荷，不能直接当作资源管理器系统消息头。

建议先建立一个自建教学resource manager与一个合法client，采用devctl自定义命令建立最小往返。
确定消息封装、大小与handler后，再增加受控畸形载荷测试；若必须直接MsgSend，应先按官方文档完成消息分发与连接契约。
不要把任意裸结构直接发送给系统资源管理器。

## 已实现

- target/lab_resmgr.c注册/dev/ipcsec-lab，权限0600，只处理本项目ECHO命令。
- client/lab_client.c检查真实应答内容，每次IPC设2秒SEND/REPLY超时；单次调用最多1000例。
- devctl载荷为16字节应用头及0至64字节数据，实际nbytes为16加实际载荷长度，非固定填满结构。
- 服务端先检查实际收到的字节、发送与回复空间，再读取应用字段；不信任nbytes自述。
- run-smoke.sh只发送合法ping和空载荷，验证服务退出、设备路径解绑、重启和再次往返。
- Deploy-QnxSmoke.ps1部署、固定SSH主机密钥、45秒主机截止、收集原始JSONL、源码及二进制哈希。

## 构建和运行

在PowerShell 7中执行scripts/Build-QnxNative.ps1。需要本机qnx800工具链；可用-SdpRoot指定其他安装位置。
在新建虚拟机运行时执行scripts/Deploy-QnxSmoke.ps1 -TargetAddress <登记的QNX虚拟机IP>。
脚本只写该实验机/data/ipcsec-lab，测试结束会停止自己创建的服务，不接管其他同名服务。
脚本移除新VM的默认路由以限制外网访问；VMnet8开发网段仍可访问，不能当成完整网络隔离证明。
如执行中断，先检查远端服务与设备状态，禁止对未知同名服务自动kill。

## 待完成

独立系统服务IPC探针、阻塞超时和完整故障影响范围、
故障对照实验、教师选题批准、伙伴复现和个人签署。当前TimerTimeout和主机截止已配置，但故意阻塞场景尚未验收。

动态撤权、文件缺失、坏格式和目标记录不匹配已在逐请求同步边界实测，见review/native-authorization-milestone.md；不覆盖在途IPC取消。
受控SIGTERM退出与新PID恢复、独立uname及只读/proc探针已实测，见review/native-recovery-milestone.md；不等于全系统故障隔离。
暂停超时切片未验收且已按连续失败规则停止注入，最新gate检查点仅编译与主机回归通过，见review/native-stall-issue.md。--controlled-pause是明确启用的实验模式，默认资源管理器不触发该检查点。

最新更新：用户重新要求继续后，专用gate检查点下2秒发送侧超时与同PID恢复已实测通过，共享停止/重启回归也通过，见review/native-stall-milestone.md。前段为历史状态，不将旧失败改为通过。

参考链接见docs/references.md。没有可用工具链时不生成伪编译成功记录。
