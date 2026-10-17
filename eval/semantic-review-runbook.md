# 语义评价接入与校准

关联 OBS-01、SEC-03、ISO-01。DeepSeek真实构造样例校准v2为10/10，有限真实材料审查v2为3/3；独立人工真值与伙伴校准仍未执行。旧拒收及截断保留，见review/deepseek-calibration-milestone.md。离线模拟transport的测试不计为模型校准。

## 冻结批次入口

```powershell
python -m ipcsec.model_calibration prepare --folder evidence/model-review-runs/<新快照>
python -m ipcsec.model_calibration execute --folder evidence/model-review-runs/<新快照>
python -m ipcsec.model_calibration verify --folder evidence/model-review-runs/<已有快照>
```

prepare不联网，冻结答案、输入、完整请求与适配器源码；execute使用独占started标记，每批最多10条、每条只调用一次，禁止隐式续跑或重试，连续三项失败停止。verify只读核验完整材料集并从原始响应重算。integrity.json为完整性哈希而非可信签名。预期答案由AI编写且不发送给模型，不能将结果称为独立准确率100%。真实材料需先本地重验并得到对外发送授权。默认1500输出token包含推理token，incomplete拒收。

2026-10-17切换：CLI默认provider为deepseek，模型显式传入deepseek-flash；登记见configs/evaluator-model.json（登记文件不自动注入CLI参数）。独立读取DEEPSEEK_API_KEY，仅发送至https://api.deepseek.com/responses；OpenAI必须显式--provider openai，使用OPENAI_API_KEY。接口依据：https://api-docs.deepseek.com/guides/responses_api/ 。

```powershell
python -m ipcsec.semantic_review --provider deepseek --model deepseek-flash --packet packet.json --run-dir build/model-review/<snapshot>/<criterion>
```

DeepSeek的store参数不受支持，官方称响应固定store=false；这不等同于数据留存政策保证。下文OpenAI示例需补--provider openai。任何供应商调用都须确认材料可发送。

接口依据：[OpenAI Structured Outputs 官方指南](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)。显式选择支持该输出格式的模型；不默认模型、不重试、不提供工具调用，store=false。网络超时45秒，输出1500 token，每个专用packet目录最多10次尝试，失败也占用预算。换目录不会形成全局计费限制，操作者仍须按快照汇总预算并检查账户用量。

## 输入与执行

构造JSON packet，字段必须且只能为 criterion_id、scope、source_version、evidence、approved_na、complete_system_probes。criterion_id限SEC-03/OBS-01/ISO-01。evidence每项字段为id、source_version、level、excerpt；level限fixture_demo/simulation/qnx_native。最多12项、每项6000字符、总计40KB。先由人核对原始manifest与真实文件，再摘录必要材料；输入校验不等于自动验证材料真实性。不要发送密钥、个人资料、SDK或未经授权材料。

```powershell
# 离线生成请求，不调用模型；输出文件须不存在
python -m ipcsec.semantic_review --packet packet.json --model <明确模型ID> --request-out request.json
# 本机安全配置DEEPSEEK_API_KEY后显式执行，密钥不要发到聊天或写入仓库
python -m ipcsec.semantic_review --packet packet.json --model <明确模型ID> --run-dir build/model-review/<snapshot>/<criterion>
```

保留packet、请求、原始响应、usage字段、验证结果或失败类型；不记录Authorization。该入口会向选定供应商发送packet，运行前确认材料允许发送。原始响应含refusal或incomplete时不接受结论。伪造引用、错版本、越范围、擅自N/A、成绩或人工签署均拒收。现有独立探针不满足完整隔离，ISO-01不得PASS。模型结论始终是建议。

## 校准流程（工程首轮已执行，独立人工复核待做）

1. 按K1—K6语义构造可读证据及保留变体，限定三个criterion；不要把旧基线的expected/observed判定标签塞进模型输入。现有CAL-01 fixtures只能用于旧确定性基线。
2. 在单独人工答案文件冻结预期结论与理由；为packet和答案记录SHA256，答案不发送给模型。保留变体由独立人员准备更佳。
3. 用明确模型及固定请求参数逐项调用，按快照最多10次预算安排校准。不能把十次请求预算误解为可容纳任意数量变体。
4. 先验证输出引用，再由人逐项比较真值、漏报、误报和不足证据处理。记录模型ID、时间、API usage、成本依据、失败和修改；任何拒收不得算PASS。
5. 修改提示词后使用未暴露变体复测，保留旧记录。模型判断未通过校准时不得进入正式E3。教师/伙伴批准由本人记录。

E2仍按review/CH-01.md的Proposed流程；本适配器不批准Change。E3可使用本入口生成审查建议，但独立伙伴执行、Finding回应及签署仍需实际完成。
