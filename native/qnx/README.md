# QNX 原生接入状态

状态：最小真实链路已实现并在新建QNX 8.0 x86_64虚拟机验证。尚未实现原生模糊测试和独立监控。
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

原生Fuzzer适配、负向畸形消息、网关防御与限流、独立进程和系统探针、故障影响及恢复时间、
对照实验、教师选题批准、伙伴复现和个人签署。当前TimerTimeout和主机截止已配置，但故意阻塞场景尚未验收。

参考链接见docs/references.md。没有可用工具链时不生成伪编译成功记录。
