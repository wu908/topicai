# TopicAI CreatorSeries 阶段实施记录

## 阶段目标

让 AI 从创作者已经发布的多篇内容中提出可能的系列关系，并把“是否属于同一系列”的最终判断留给创作者。

本阶段的产品边界是：

> AI 可以提出“这些内容可能值得连续讲”，只有用户确认后，系统才能把它用于后续内容决策。

## 来源资格

一个系列候选必须同时满足：

- 来源属于同一用户。
- 来源项目至少 2 个、最多 20 个，且不可重复。
- 每个项目已经真实发布，并保留锁定发布版本和 PublishRecord。
- 每个项目的内容意图已经确认。
- 所有来源项目的 `content_intent` 和 `content_format` 一致。
- 项目没有删除或归档。

草稿、待发布项目、跨用户项目和不同意图/形式项目不能组成首版系列候选。

## 核心决策

- 新增 `CreatorSeries` 候选实体和追加式事件审计。
- AI 输出系列名称、共同读者价值、关系理由和下一篇延展方向。
- 模型不可用时只保存用户选中的项目关系，不根据标题猜测共同主题。
- 用户可以取消不相关来源项目，并编辑候选后确认、拒绝或撤销。
- 只有 confirmed 且全部来源项目仍有效的系列进入 CreatorState、ContentGenome 和后续行动引用。
- 不自动创建下一篇项目，不自动排期，不自动把新内容并入系列。
- 不扩展 ContentProject 状态机，也不推断创作者声音模式。

## 数据与审计

迁移 `026_creator_series.sql` 新增：

```text
creator_series
creator_series_events
```

状态生命周期：

```text
proposed -> confirmed -> revoked
         -> rejected
```

每个候选保存完整的来源项目引用、意图和形式范围、候选与确认值、AITrace、生成方式、限制、版本及幂等键。确认时再次校验全部来源，防止候选生成后项目被归档或发布依据失效。

## ContentGenome 增量

新增节点和关系：

```text
content_project --part_of--> creator_series
```

新增输出：

```text
series_context[]
summary.applicable_series_count
```

confirmed 系列可用于相同意图和内容形式的当前项目，不要求当前项目已经发布。来源项目后续失效时，系列历史节点保留并标记 `needs_review`，失效关系边标记 `invalidated`，系列退出 `series_context`。

ContentGenome 指纹包含系列节点状态，因此确认、撤销或来源失效都会使旧 NextBestAction 被替换。

## CreatorState 与 Orchestrator

- 用户确认后，CreatorState 增加 `creator-series:{id}` 的 validated insight。
- 用户撤销系列后，该引用从 CreatorState 移除，系列和事件历史不删除。
- NextBestAction 和 AITrace 引用 `creator-series:{id}`，不复制来源项目正文。
- Orchestrator 的 visibility boundary 显式记录 `user_confirmed_series`。

## 前端行为

内容项目工作台新增“内容系列”：

- 只列出与当前项目同意图、同形式的已发布内容。
- 默认选中最近最多 20 个可用来源，用户可以取消不相关项目。
- 少于 2 个来源时不能生成候选。
- 有待确认候选时禁止继续堆积候选。
- 候选名称、共同价值和下一篇方向均可编辑。
- confirmed 系列单独展示并支持撤销。

## API 契约

```text
GET  /api/v2/creator-series
POST /api/v2/creator-series-candidates
POST /api/v2/creator-series/{series_id}:decide
POST /api/v2/creator-series/{series_id}:revoke
```

创建、确认、拒绝和撤销均具备 owner isolation、幂等重放和乐观版本校验。
确认与撤销的幂等重放同时校验 `series_id`，不会把同一个用户下其他系列的事件误判为当前请求；重放还会幂等修复 CreatorState 回写，避免数据库决策已提交但事务后状态同步失败时长期不一致。

## 验证结果

- 迁移与完整表集合契约：26 passed。
- 系列服务生命周期定向测试：6 passed。
- 系列 API、OpenAPI、服务与迁移联合定向测试：14 passed。
- 前端工作台定向测试：8 passed。
- 前端内容页定向测试：6 passed。
- 后端全量：744 passed。
- 覆盖率门禁使用每次运行隔离的 pytest 临时目录，避免旧运行目录 ACL 污染下一次验收。
- 前端全量：50 files、337 passed、2 skipped。
- 前端 lint：通过。
- 前端 production build：通过。

## 未进入本阶段

- 不自动生成或发布下一篇内容。
- 不自动把未来项目加入已确认系列。
- 不使用标题相似度直接确认系列。
- 不跨意图、跨形式或跨账号建立系列。
- 不自动合并相似系列或解决系列冲突。
- 不推断声音、人格或语气指纹。

## 下一阶段建议

confirmed 系列产生“下一篇延展机会”的阶段已经完成，详见 [系列延展机会阶段实施记录](./series-extension-opportunity-stage-2026-07-21.md)。下一步应把机会接入“今日”的唯一 NextBestAction，且不得覆盖临近发布、待确认或待复盘任务。
