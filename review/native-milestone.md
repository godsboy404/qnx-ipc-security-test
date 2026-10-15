# QNX真实合法IPC里程碑

日期：2026-10-15，Asia/Shanghai。状态：本机真实链路已验证；教师审批、伙伴复现与个人签署仍为pending。

## 本轮结果

| 项目 | 结果与证据 |
| --- | --- |
| QNX虚拟机 | 官方mkqnximage生成，VMware运行QNX 8.0.0 x86_64 |
| 工具链 | qcc 12.2.0，gcc_ntox86_64；C11及_QNX_SOURCE，Wall Wextra Werror编译通过 |
| Hello部署运行 | 输出Hello QNX: course toolchain smoke test |
| 自建资源管理器 | lab-resmgr注册/dev/ipcsec-lab，devctl ECHO |
| 首轮合法请求 | 100条ping全部返回码0、内容核对PASS |
| 合法空载荷 | 1条，应用头16字节，payload为0，PASS |
| 服务停止与重启 | 原进程退出、设备解绑，再启动服务；100条ping全部PASS |
| 第二次完整运行 | 新增主机45秒截止及二进制哈希后，再次100加1加100全部通过 |
| 主机回归 | 9项通过 |
| 基线快照 | IPC-Ready-20261015创建成功，VMware列表确认存在 |
| 快照恢复 | 已执行回滚并启动，临时标记消失、Hello再次运行，SNAPSHOT_RESTORE_OK |

## 原始证据

- 首次运行：evidence/native-runs/20261015T104103Z-441179b4/。
- 完整索引运行：evidence/native-runs/20261015T104537Z-afa1f753/。
- 每个目录保留hello.txt、normal.jsonl、empty.jsonl、restarted.jsonl、服务日志、目标信息及manifest。
- 第二次manifest包含45秒主机截止参数、源码和脚本哈希、3个部署二进制哈希及原始文件哈希。
- 快照恢复输出：review/snapshot-restore.txt。
- 核验命令：python scripts/verify_native_evidence.py，两份运行均核验201条结果及完整性通过。

所有结果来源为本机SSH runner，不冒充peer_runner或教师结果。哈希证明文件一致性，不能替代独立执行复核。

## 环境与网络处理

本机Host-only网卡无IP，未修改Windows网卡，改用已有VMnet8开发连接。VM地址从匹配该VM的DHCP租约取得。
部署后删除Guest默认路由，第二次target-info.txt确认只保留本地IPv4路由，没有IPv4默认路由。
这不保证所有网络路径隔离，也不授权测试同网段其他设备。
SSH使用项目专用密钥及构建时生成的主机公钥严格校验。VM磁盘、内存、密钥和产物均在忽略目录build中。

## 发现与处理

- 受限沙箱阻止QNX Bash和虚拟网络连接，经系统批准后使用官方工具完成构建与部署。
- 严格C11构建未自动开放QNX扩展，SETIOV链接失败；核查本机头文件后显式启用_QNX_SOURCE，保留Werror。
- 首次Windows OpenSSH协商出现Corrupted MAC；改用双方支持的AES128-CTR和HMAC-SHA256后部署成功。
- VMware回滚后可能处于关机状态，脚本已增加显式启动步骤。
- 恢复后的SSH一度返回Not allowed at this time；保留防护配置，等待后重新连接成功。未把连接异常写作QNX崩溃。
- 首次回滚创建并验证了标记，回滚后通过VerifyOnly确认其消失和Hello执行；没有为修复SSH禁用安全检查。

## 当前边界和下一步

当前为用户授权的本机自建目标合法路径开发。未运行真实畸形消息、系统服务攻击、崩溃注入或跨进程隔离实验。
服务端虽有字段与实际消息长度检查，本轮仅验收合法请求，不能据此声称负向输入防御已全面通过。
客户端2秒SEND/REPLY超时、主机45秒截止已配置，故意阻塞触发与取消行为尚需后续实验。
Python QnxTransport仍未接原生后端，模拟和原生证据目录独立。

下一步：实现独立目标与客户端探针、真实超时分类和恢复；再将固定有界变异接入自建接口，完成负向验收及防御对照。
本轮未推送GitHub，未上传镜像或密钥。当前VM保持运行，Smoke结束后自建测试服务已停止。
