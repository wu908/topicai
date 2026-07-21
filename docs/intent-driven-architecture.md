# TopicAI 意图驱动架构冻结

## 产品定义

TopicAI 先理解一条内容想产生的影响，再将它变成适合该意图的创作、发布和复盘行动。

首版只支持小红书，内容意图为 `solve`（解决）、`share`（分享）、`record`（记录）。图文是可发布格式；`vlog_plan` 只提供记录型内容规划，不提供视频剪辑。

## 职责边界

AI 负责读取创作者状态和项目证据、识别候选意图、发现证据缺口、选择唯一下一步、准备候选内容与复盘任务。用户只确认事实、意图、表达、公开范围、发布和长期经验写入。

默认模式为 `guided`。满足三个已完成项目、候选接受率不低于 80%、没有未处理的事实或隐私纠正且用户明确同意后，项目可使用 `autopilot_to_ready`。任何模式均禁止自动发布、自动公开素材、覆盖已确认版本或自动写入长期经验。

## 三条意图链路

| 意图 | 观众变化 | 最低证据 | 内容结构 | 复盘信号 |
|---|---|---|---|---|
| 解决 | 从不知道怎么做到能开始行动 | 问题场景、本人方法、案例或限制 | 问题 → 方法 → 案例 → 行动 | 收藏、关注、问题型评论 |
| 分享 | 从不了解到产生理解或共鸣 | 真实事件、感受或观点、形成原因 | 事件 → 感受/观点 → 意义 | 共鸣评论、互动质量、关注变化 |
| 记录 | 从看到一个时点到愿意持续关注变化 | 起点、过程证据、转折、当前结果 | 起点 → 过程 → 转折 → 结果 | 阅读完成、持续关注、系列继续率 |

## 技术边界

- `ContentProject` 仍是聚合根；新增 `content_format` 表示内容规划形式，旧 `format` 继续表示当前实际发布格式，避免破坏只允许图文的旧发布链路。
- 旧项目迁移为 `content_intent=solve`、`intent_status=legacy_missing`，必须由用户确认后才能成为已确认意图。
- `NextBestAction` 是显式、可审计、可过期的行动记录；旧存在性状态机只作为 `fallback_action`。
- `HumanGate` 保护不可逆动作；确认请求必须有幂等键和版本检查。
- `ai_traces_v2` 继续记录输入、证据、可见范围、限制和输出引用。

## Evidence 确认边界

`Evidence` 是内容项目和创作者长期状态之间的安全边界。采访回答先进入 `proposed`，并带有 `source_ref`、`privacy_level`、项目归属和幂等键；它不能直接成为 `CreatorState.facts`，也不能被候选版本引用。

只有 `user_fact` HumanGate 确认后，Evidence 才变为 `confirmed + reusable`。此时系统才可以创建候选版本并将其写入 CreatorState。拒绝进入 `rejected`，撤销进入 `revoked`；两者都不能继续生成或锁定事实型发布版本。撤销会使未发布的相关发布假设失效，已发布版本只保留历史快照。

这条边界同时适用于 AI 生成和手工路径：AI 超时可以让用户手工补充回答，但手工回答仍必须经过同一确认门；`ai_inference` 永远不能直接升级为用户事实。
- `CreatorState` 分开存储用户事实、AI 推断、已验证经验、未知和矛盾；只有确认后的长期经验可进入 `validated_insights`。

## API 契约

- `GET /api/v2/today`：返回当前唯一行动和 CreatorState 摘要。
- `GET /api/v2/creator-state`：返回带来源和版本的创作者状态。
- `POST /api/v2/projects/{id}/intent:confirm`：确认或纠正内容意图。
- `POST /api/v2/actions/{id}:respond`：接受、暂缓或切换到同任务手动路径。
- `POST /api/v2/human-gates/{id}:decide`：确认或拒绝不可逆动作。
- `GET /api/v2/projects/{id}/evidence`：查看当前项目的证据状态和来源。
- `POST /api/v2/evidence/{id}:decide`、`POST /api/v2/evidence/{id}:revoke`：执行证据确认、拒绝和撤销；内容工作台通常优先通过 HumanGate 调用。

所有 AI 行动必须返回依据、未知、预计投入、预期状态变化、确认门和手动降级路径。
