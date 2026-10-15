# QNX开发环境确认记录

确认日期：2026-10-15。执行来源：本机只读检查及交叉编译，非QNX目标运行。

## 已确认

- QNX Software Center安装目录：`C:/QNX/QNX Software Center`，已打开安装管理界面。
- Momentics IDE安装目录：`C:/QNX/qnxmomenticside`。
- SDP目录：`C:/Users/zrz51/qnx800`。
- 编译器：`host/win64/x86_64/usr/bin/qcc.exe`。
- 环境脚本：`qnxsdp-env.bat`及`qnxsdp-env.sh`。
- `qcc -V`成功，列出12.2.0的gcc_ntox86_64和gcc_ntoaarch64le等配置。
- 临时设置当前编译进程的QNX_HOST、QNX_TARGET及工具PATH后，x86_64编译链接成功。
- 源文件：`native/qnx/client/hello_qnx.c`。
- 构建参数：`qcc -Vgcc_ntox86_64 -Wall -Wextra -o build/toolchain-check/hello-qnx-x86_64 native/qnx/client/hello_qnx.c`。
- `ntox86_64-readelf -h`确认产物为64位小端x86-64 ELF。
- 构建目录被.gitignore排除；未更改Windows永久环境变量。

当前默认终端未加载QNX环境，并不表示未安装工具链。早期environment-check中qcc_on_path为null仅表示PATH未配置。
此次编译成功不代表所有SDK组件、架构或未来操作均已验证，也未检查或披露许可证密钥。

## 尚未具备

用户确认尚未创建QNX目标系统。暂未在QNX上执行Hello程序，也未验证resource manager、合法IPC、探针、快照或恢复。
下一步是选择并建立QNX 8.0虚拟机或开发板目标，确认架构与SDK匹配，再部署Hello并验证运行。
创建目标之后再进入TASK-01的100次合法IPC往返门，不使用Windows执行该ELF程序。

本次仅确认工具链与目标状态，未安装新软件、创建虚拟机或变更网络及安全设置。
