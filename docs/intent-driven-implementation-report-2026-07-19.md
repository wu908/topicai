# TopicAI 意图驱动垂直切片实现报告

## 1. 本轮结论

本轮把 TopicAI 的主入口从“旧工具与人工状态机”改为可运行的意图驱动行动闭环。系统现在持久化唯一下一步、依据、未知、预计投入、手动降级和人工确认门；用户确认后由后端推进项目，而不是要求用户理解 `Brief`、`PublishHypothesis` 或 `Observation` 等内部对象。

这仍是 MVP 垂直切片，不代表 `009-ai-native-action-loop` 全部完成。规则版本、实验分析、删除/导出和自动准备模式完整 UI 仍是后续工作。

## 2. 已实现范围

### 2.1 内容意图

- `solve`：解决一个具体问题。
- `share`：分享经历、观点或感受。
- `record`：记录过程、变化和结果。
- 新项目可让系统根据标题线索给出候选意图，也可由用户显式选择。
- 旧项目映射为 `solve + legacy_missing`，必须重新确认，旧数据不删除。
- 三种意图分别改变关键问题、真实素材要求、预期反应和复盘信号。

### 2.2 后端行动闭环

- 新增 `CreatorStateService`，区分用户事实、AI 推断、已验证经验、未知和矛盾。
- 新增持久化 `NextBestAction`、`HumanGate` 和 `ActionEvent`。
- 每个行动包含理由、证据引用、未知、预计投入、预期变化、自动化等级、人工确认门、过期时间和手动降级。
- 行动、意图确认和确认门均使用幂等键与版本检查。
- 复用现有不可变 `ContentVersionService` 和原子 `PublishHypothesisService`。
- 用户回答一个关键真实问题后，系统准备候选内容；模型不可用时生成明确标注限制的结构骨架，不编造经历。
- 候选内容确认通过 `HumanGate`，确认后锁定发布版本并停在用户发布前。
- 复用 `ai_traces_v2` 记录输入范围、证据、限制和输出引用。

### 2.3 前端主链路

- 今日页只显示一个真实行动，不再显示伪造阅读量、关注量、热度建议或旧工具按钮。
- 今日行动展示“为什么现在做、AI 依据、还不知道、预计投入、自动化模式和人工确认要求”。
- 支持进入行动、暂缓和手动继续。
- 内容列表显示内容意图和用户可读下一步，不显示内部技术动作。
- 项目创建允许只有模糊想法，不强制先填写目标读者。
- 项目工作台按内容意图解释目的、素材和复盘方式。
- 意图确认、关键问题、候选内容确认成为项目内主行动。
- 全局五节点导航保持为 `今日｜内容｜机会｜素材｜我的`。
- 移除旧全局右侧“发现新选题”入口，避免同屏出现第二个主行动。

### 2.4 Evidence 证据闭环

- 新增 `evidence_items` 作为用户事实、外部事实、AI 推断和已验证经验的统一证据实体；回答不再直接写入 `CreatorState`。
- 采访回答先创建 `proposed` Evidence，并自动打开 `user_fact` HumanGate；用户确认后才创建候选 `ContentVersion`、写入 CreatorState，并推进到候选内容确认。
- 用户拒绝 Evidence 后，证据保持 `rejected`，不会进入 CreatorState，系统生成新的采访行动；旧行动不会因幂等键冲突阻塞重试。
- 用户撤销已确认 Evidence 后，相关未发布候选的锁定假设会失效，发布锁定会被清除；已发布历史仍保留原有版本快照。
- 候选版本只允许引用 `confirmed + reusable` Evidence；发布前重新校验证据，避免撤销后继续锁定。

### 2.5 意图专属复盘与经验确认

- 盲评结果现在保存 `intent_review`：观察事实、可能原因、继续一项、停止一项和实验一项。
- `solve`、`share`、`record` 使用不同的观察信号和实验方向，不能用一次统一指标替代内容意图。
- `confirm_learning` 使用 `long_term_learning` HumanGate；用户拒绝不会创建 Observation，用户确认后才保存一条带完整计划范围的 Observation。
- 一次复盘不会直接写入 CreatorState，也不会激活长期规则。

### 2.6 跨样本经验与规则版本

- 新增 `creator_rules`、`creator_rule_versions` 和 `creator_rule_events`，记录规则聚合、不可变版本和确认/拒绝/回滚审计。
- 只有至少两条同意图、同实验语义且未被证伪的 Observation 才能形成规则候选。
- 候选确认后才写入 `CreatorState.validated_insights`；拒绝不会污染长期经验。
- 回滚只切换当前激活版本，不修改历史版本、Observation 或来源快照。

## 3. 数据与兼容

迁移 `020_intent_driven_actions.sql` 与 `021_evidence_items.sql`：

- 扩展 `content_projects`：`content_intent`、`content_format`、`intent_status`、`audience_change`、素材/反应/信号、`automation_level`、`creator_state_version`。
- 新增 `creator_states`、`next_best_actions`、`human_gates`、`action_events`。
- 新增 `evidence_items`；不删除 020 中的旧字段和记录。
- 新增 `content_segments` 与 `content_segment_decisions`；候选片段和用户决定均按项目、版本和所有者隔离。
- 继续使用 `ai_traces_v2`、`content_versions`、`publish_hypotheses`、发布记录、指标快照、盲复盘和观察表。
- `content_format` 表示规划形式；旧 `format` 继续表示实际发布格式，避免破坏首版图文约束。

## 4. 新增 API

- `GET /api/v2/today`
- `GET /api/v2/creator-state`
- `GET /api/v2/projects/{project_id}/next-action`
- `POST /api/v2/projects/{project_id}/intent:confirm`
- `POST /api/v2/actions/{action_id}:respond`
- `POST /api/v2/actions/{action_id}/human-gate`
- `POST /api/v2/human-gates/{gate_id}:decide`
- `POST /api/v2/projects/{project_id}/automation`
- `GET /api/v2/projects/{project_id}/evidence`
- `POST /api/v2/evidence/{evidence_id}:decide`
- `POST /api/v2/evidence/{evidence_id}:revoke`
- `GET /api/v2/projects/{project_id}/candidate-review`
- `POST /api/v2/projects/{project_id}/candidate-review/segments/{segment_id}:decide`
- `POST /api/v2/projects/{project_id}/candidate-review:revise`
- `POST /api/v2/projects/{project_id}/candidate-review:restore`

## 5. 验证结果

- 后端全量回归：723 项通过；其中意图/Evidence API、候选评审、发布假设和盲复盘、迁移/单一 schema 均通过。
- 三种意图问题分支、旧项目映射、短回答拒绝、候选生成、逐段评审、意图复盘计划、长期经验 HumanGate 和发布锁定均有 API/服务测试。
- 迁移测试：fresh apply、重复执行、从 019 升级到 021 共 4 项通过。
- 前端 `npm run build` 和 `npm run lint` 通过。
- 前端全量测试：49 个文件通过，328 项通过，2 项按原配置跳过；`npm run lint` 和 `npm run build` 通过。
- 意图复盘计划和长期经验确认门测试通过；三种意图均验证了继续/停止/实验三项输出。
- 覆盖率门槛子套件通过。
- 浏览器桌面验证：唯一行动、依据/未知、意图确认、采访回答、刷新后 Evidence 确认、候选确认、发布前停止均通过。
- 浏览器移动端验证：390×844 下逐段候选评审和意图复盘确认门均可见，无横向溢出，任务、确认按钮和底部导航无重叠；控制台无应用错误。
- 浏览器控制台没有应用错误；仅存在 React Router v7 未来选项警告。

## 6. 明确未完成

- `ContentGenome` 已作为规则、例外和 Observation 的派生只读投影接入；`Experiment` 独立实体、导出删除全链路仍未实现。
- 当前行动优先级以最近活动项目为主，尚未加入周目标、投入时间、紧急度和多项目机会成本评分。
- AI 负责候选内容准备；下一步选择首版使用可审计确定性策略，尚未开放模型重排。
- 候选内容现已支持标题/正文分段、逐段接受/拒绝/替换、父版本差异对比、恢复和发布锁定前服务端门禁；旧版本仍保持不可变。
- 长期经验确认门已接入 Observation 创建；跨样本升级、规则版本和回滚仍未实现。
- 自动准备模式有后端信任门槛，尚未完成设置页入口和完整越权测试。
- 删除、导出和隐私授权的端到端影响链尚未实现；Evidence 撤销和未发布候选失效已实现，发布历史保留快照。
- ContentGenome 当前覆盖已验证规则、规则例外、Observation 来源、用户确认的 Evidence/项目关系、显式确认的 CreatorViewpoint 和 CreatorSeries；声音模式节点仍未实现。

## 7. 下一实施顺序

1. 用真实用户验证 ContentGenome 引用是否降低决策成本，并观察规则被暂缓/纠正的比例。
2. 用真实用户验证首次行动时间、手动决策数、意图纠正率、候选确认率和复盘完成率。
