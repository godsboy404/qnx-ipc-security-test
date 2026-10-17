# 本地交接准备记录

日期：2026-10-17。范围：当前源码、证据核验和课程交接材料，不是外部发布或教师验收。

已实现只读交接审计与本地ZIP构建/复核。选择7项历史技术证据、3组同版本对照重新核验；历史manifest和首轮暂停事后日志检查完整性，单列5轮FAIL/INCOMPLETE，不掩盖未通过实验。
42项主机回归通过，其中交接测试验证了路径越界拒绝、密钥/VM/build排除、保留失败、篡改包拒绝、缺证据不能通过及历史manifest引用必须完整入包。未为本轮再次注入原生故障或把AI自检冒充独立伙伴复现。

新增资产：release/partner-reproduction.md、review/partner-reproduction-record.md、release/submission-checklist.md、release/course-report-draft.md；补齐连续性、角色签署和演示入口。记录模板全部NOT_RUN或pending，真实姓名和贡献不预填。
交接包输出build/handoff/唯一目录，附包内容manifest、当前源码快照、技术审计及SHA256SUMS。包不含SDK、VM、编译产物、SSH身份或.git。SHA256用于一致性，不是身份认证或第三方背书。
历史manifest记录的源码可能与当前快照不同；审计显示匹配数量，包不重建缺失历史源码或二进制。伙伴应在新目录基于当前快照构建并生成新运行，而非宣称重建全部历史版本。

课程Gate为PENDING，伙伴复现false。正式E2 Change、独立E3、评价Agent模型接入/真实材料校准、教师批准和个人签署仍待完成。若课程接受收缩范围，须人工批准并记录，不能由AI代填不适用。

打包自检负结果：第一版20261017T140229Z-a3a7e0e6虽通过ZIP自身文件哈希，但独立解压审计发现过滤器漏掉旧Smoke的.log/.stderr依赖。该草稿不作为通过交付；修复后保留日志，并在打包前和verify-bundle中逐一校验内嵌历史manifest引用，防止仅验证已入包文件而漏掉依赖。第一版原件不覆盖，后续另建目录重新打包。
