# TopicAI 跨内容规则冲突阶段实施记录

## 阶段目标

在“至少两条可比较 Observation 才能形成长期经验”的基础上，补齐规则适用范围比较、同意图冲突提示和跨意图隔离，避免系统把局部经验错误扩展为所有内容的通用结论。

## 产品决策

- 内容意图是规则隔离的第一层边界。`solve`、`share`、`record` 之间不互相判定冲突。
- 规则适用范围由 `content_intent`、`experiment`、`audience`、`format` 四个维度组成。
- 某一维度缺失时，该规则在该维度上被视为较宽泛；但缺失意图时不参与冲突匹配。
- 同一意图下，实验、受众和形式均不存在明确排斥时，规则被标记为适用范围重叠。
- 冲突检测只提供可解释警告，不自动删除、覆盖或合并规则，也不绕过用户确认。
- 规则版本和 Observation 继续保持不可变；回滚仍通过切换 `active_version_id` 实现。
- `CreatorState.validated_insights` 对同一 `rule_id` 只暴露当前激活版本；旧版本历史保留在规则版本和事件中，不再同时进入 AI 上下文。

## 实现范围

后端 `CreatorRuleService` 新增：

- 适用范围标准化。
- 保守的范围重叠判定。
- 待确认候选和当前生效规则的冲突列表。
- 冲突证据，包括规则、当前版本、陈述、适用范围和原因码。
- 激活或回滚时按 `rule_id` 原子替换 CreatorState 中的当前规则引用。

前端内容工作台新增：

- 待确认候选的冲突警告。
- 当前生效规则的冲突对照陈述。
- 观察状态和规则操作在移动端的纵向布局。

## 契约增量

`CreatorRuleVersion` 增加可选 `conflicts`；`CreatorRule` 增加 `conflicts`。单条冲突包含：

```text
rule_id
rule_key
content_intent
active_version_id
statement
applicability
reason = same_intent_and_overlapping_applicability
```

该增量来自现有 `scope_json` 的派生结果，不新增数据库表，也不修改历史规则数据。

## 验证结果

- 规则定向测试：4 passed。
- 迁移与 schema 单一事实源定向测试：26 passed。
- 覆盖率门禁独立复跑：1 passed；内部全量测试返回 0；总覆盖率保持高于 80%。
- 后端全量测试：727 passed，58 warnings；总覆盖率 85.57%。
- 前端 lint：通过。
- 前端 production build：通过。
- 浏览器移动端烟测：390px 下 `scrollWidth === clientWidth`，无横向溢出。
- 浏览器契约烟测：规则冲突提示和冲突规则陈述均可见。
- 冲突处理浏览器烟测：三个处理动作均可见；缩小范围对话框可打开；390px 下无横向溢出。
- 前端冲突处理定向测试：2 passed；前端全量：50 files、330 passed、2 skipped。
- 真实开发数据库已加载 `024_creator_rule_resolutions`，OpenAPI 已暴露冲突处理接口。
- 后端全量测试必须使用仓库根目录下的直接 `--basetemp` 路径；系统默认临时目录没有访问权限。

本阶段为迁移测试契约同步新增了 `creator_rule_resolutions` 表的升级顺序、schema 期望集合和回放断言；未修改历史迁移，也未删除或重写既有数据。

## 冲突处理增量

迁移 `024_creator_rule_resolutions.sql` 新增审计表，支持三种用户确认动作：

- `narrow_scope`：至少补充一个实验、受众或形式条件，生成新的 active 规则版本。
- `keep_exception`：记录这组规则可以并存的例外决定，冲突显示为已确认例外。
- `deactivate`：停用当前规则，历史版本和 CreatorState 来源记录仍保留。

接口：

```text
POST /api/v2/creator-rules/{rule_id}/conflicts/{conflict_rule_id}:resolve
```

所有动作都要求双方规则版本号和幂等键。范围缩小不能改变内容意图、不能放宽已有范围，且提交后必须不再与冲突规则重叠。

前端在规则卡片中提供“保留为例外”“缩小适用范围”“停用当前规则”，缩小范围使用对话框收集条件，不暴露内部 JSON。

## 后续边界

本阶段不做自动规则合并，也不使用向量相似度猜测语义冲突。`ContentGenome` 已在下一阶段作为只读投影实现；后续继续扩展图谱节点类型时，仍必须保持规则版本、Observation 和用户确认链路可追溯。
