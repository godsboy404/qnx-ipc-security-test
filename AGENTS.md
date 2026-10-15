# 项目工程规则

先读 docs/intent.md、docs/specification.md、docs/acceptance-matrix.md 和 docs/harness-manifest.md。
当前Intent、Spec和CH-01均为草案；用户授权建设目录与起步工程，不等于教师批准选题或真实目标测试。

- 主机模拟使用 ipcsec/，QNX原生适配使用 native/qnx/，不可混淆证据来源。
- 只测试明确登记并获授权的自建目标；默认不提供网络、任意Shell或系统服务测试接口。
- 测试配置、验收和源代码变更应关联Req ID；旧运行证据不可编辑或冒充新版本证据。
- 不能用timeout推断crash；没有独立探针时隔离结果必须为INCONCLUSIVE。
- 校验失败不得通过删除测试或降低规格解决；连续三次相同关键失败时保存证据并记录人工问题。
- 未经批准不进行生产部署、真实服务扫描、敏感数据接入或破坏性变更。
- 验证：python -m unittest discover -s tests -v；python -m ipcsec demo；python -m ipcsec calibrate。
- 构建QNX前先检查qcc与授权、架构、快照、重置及外部watchdog；当前原生代码只有协议草案。

模型可生成建议和候选代码。范围、业务语义、证据结论、签署由人决定。
