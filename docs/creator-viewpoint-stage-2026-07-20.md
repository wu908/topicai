# TopicAI CreatorViewpoint 阶段实施记录

## 阶段目标

让 AI 能从用户已确认的真实素材中提出观点候选，同时保证候选不会被静默当成创作者长期立场。

本阶段冻结的产品边界是：

> AI 可以提出“这可能是你的观点”，只有用户编辑并确认后，系统才能说“这是你的观点”。

## 核心决策

- 新增 `CreatorViewpoint` 候选实体和追加式事件审计。
- 候选只能引用当前项目 ContentGenome `evidence_context` 中允许使用的 confirmed Evidence。
- 模型可用时调用结构化生成；模型不可用时原样保留一条已确认陈述，不扩写新主张。
- 用户可以编辑后确认、直接拒绝或撤销已确认观点。
- 只有 `confirmed` 且来源 Evidence 仍有效的观点进入 `viewpoint_context` 和后续行动引用。
- 不自动聚类、合并观点，不推断声音模式，不扩展 ContentProject 状态机。
- 不强行扩展现有 HumanGate 枚举，复用 CreatorRule 的显式 decision 与 append-only event 模式。

## 数据与审计

迁移 `025_creator_viewpoints.sql` 新增：

```text
creator_viewpoints
creator_viewpoint_events
```

状态生命周期：

```text
proposed -> confirmed -> revoked
         -> rejected
```

每个候选保存：候选陈述、生成理由、意图与适用范围、来源 Evidence 引用、可选内容版本引用、隐私级别、生成方式、AITrace、限制、版本与幂等键。

确认时再次校验来源 Evidence，防止“提出候选后来源被撤销、仍写入长期状态”的竞态。

## ContentGenome 增量

新增节点和关系：

```text
creator_viewpoint --derived_from--> evidence
creator_viewpoint --belongs_to--> content_project
```

新增输出：

```text
viewpoint_context[]
summary.applicable_viewpoint_count
```

`proposed`、`rejected` 和 `revoked` 不进入图谱。confirmed 观点的来源 Evidence 后续失效时，历史节点保留并标记 `needs_review`，`derived_from` 边标记失效，观点不再进入 `viewpoint_context`。

ContentGenome 指纹包含观点节点状态，因此观点确认、撤销或来源失效都会使旧 NextBestAction 被替换，后续 AITrace 不再引用过期观点。

## CreatorState 与 Orchestrator

- 用户确认后，CreatorState 增加 `creator-viewpoint:{id}` 的 validated insight。
- 用户撤销观点后，该引用从 CreatorState 移除，观点和事件历史不删除。
- NextBestAction 和 AITrace 只保存 viewpoint/evidence 引用，不在审计引用字段复制观点正文。
- Orchestrator 的 visibility boundary 明确记录 `user_confirmed_viewpoints`。

## 前端行为

内容项目工作台的“本次 AI 实际参考”区域新增“你的观点”：

- 没有已确认素材时，只显示需要先确认素材的状态。
- 有可用素材时，用户可以发起“提炼候选”。
- 同时只允许处理已有待确认候选，避免批量堆积。
- 候选标记为“AI 候选 · 尚未确认”，允许编辑后确认或拒绝。
- 已确认观点单独展示并支持撤销。
- 用户不需要进入独立工具页，观点始终属于当前内容项目和同一条创作链路。

## API 契约

```text
GET  /api/v2/creator-viewpoints
POST /api/v2/projects/{project_id}/viewpoint-candidates
POST /api/v2/creator-viewpoints/{viewpoint_id}:decide
POST /api/v2/creator-viewpoints/{viewpoint_id}:revoke
```

创建、确认、拒绝和撤销均具备 owner isolation、幂等重放和乐观版本校验。

## 验证结果

- 观点服务、迁移和关联回归定向测试：46 passed。
- 观点 API 与 OpenAPI 定向测试：4 passed。
- 前端观点组件与页面命令定向测试：2 files、11 passed。
- 后端全量：736 passed。
- 前端全量：50 files、334 passed、2 skipped。
- 前端 lint：通过。
- 前端 production build：通过。

## 未进入本阶段

- 不从正文自动生成并确认观点。
- 不自动合并相似观点或解决观点冲突。
- 不推断“创作者声音”“人格”“语气指纹”。
- 不把观点公开给其他用户或用于跨用户训练上下文。
- 不自动发布，不自动写入已确认正文。

## 下一阶段建议

“系列关系候选”已经完成，详见 [CreatorSeries 阶段实施记录](./creator-series-stage-2026-07-21.md)。声音模式继续后置，至少需要多条用户确认文本、稳定跨项目证据和独立撤销机制，避免把短期措辞误判为身份特征。
