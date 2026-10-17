# 目录职责

hello_qnx.c、lab_client.c及lab_fuzzer.c已完成原生运行。Fuzzer读取固定格式语料，实际payload最多65字节、最多200例，逐次记录字段、返回码和单调时间；每次devctl设2秒超时。主机ipcsec/native.py使用独立oracle校验结果并支持保留原始字段的单例重放。

schema_version=2增加lab_policy.h客户端网关：逐请求读取authorization.txt，defense模式校验输入并按八个受限会话限流；baseline模式仍检查授权。输出decision、forwarded和NOT_SENT，结合独立target-audit.jsonl核验真实转发。该客户端策略不是强制系统拦截；运行方法见release/native-fuzz-runbook.md。

authorization场景使用带-auth的模式文件，要求监督进程逐请求确认授权变更后再读取权限；确认最多等待2秒，失败不继续IPC。缺文件、坏格式、目标记录不符以及动态撤销均按SCOPE_DENY处理。
