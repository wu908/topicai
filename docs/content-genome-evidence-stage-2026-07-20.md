# TopicAI ContentGenome Evidence 阶段实施记录

## 阶段目标

把用户已经确认的事实、案例和其他 Evidence 接入 ContentGenome，让 AI 的下一步行动同时具备“为什么这样做”的规则依据和“可以使用什么真实素材”的证据依据。

本阶段继续坚持只读投影：`evidence_items` 是证据事实源，ContentGenome 不复制正文、不创建第二套素材表。

## 使用边界

- 当前项目内：`confirmation_status=confirmed` 的证据可用于当前项目，包括敏感证据。
- 跨项目：必须同时满足 `confirmed`、`reusable=true`、非 `sensitive`、内容意图一致且内容形式一致。
- `proposed`、`rejected` 和 `revoked` 证据不进入图谱行动上下文。
- 敏感证据即使标记为可复用，也不默认跨项目传播。
- AITrace 和行动记录只保存 `evidence:{id}`，不保存证据陈述正文。
- 证据撤销后，图谱指纹变化，旧行动被 supersede，新行动不得继续引用该证据。

## 图谱增量

新增节点：

```text
evidence
content_project
```

新增关系：

```text
evidence --belongs_to--> content_project
observation --observed_in--> content_project
```

ContentGenome 输出新增：

```text
evidence_context[]
summary.applicable_evidence_count
```

单条 `evidence_context` 包含证据引用、陈述、来源类型、隐私级别、来源项目、复用状态和进入上下文的原因。

## Orchestrator 行为

- `NextBestAction.evidence_refs` 同时包含适用 CreatorRule 和已确认 Evidence 引用。
- `expected_state_change.content_genome_fingerprint` 同时反映规则和证据状态。
- AITrace 的实际边界区分 `confirmed_creator_rules` 和 `confirmed_reusable_evidence`。
- 证据陈述只在用户自己的工作台读取，不进入通用分析埋点。

## 前端行为

内容项目工作台的“本次 AI 实际参考”区域新增“本次可使用的已确认素材”：

- 区分当前内容素材与可复用历史素材。
- 敏感素材仅在当前项目显示，并标记“仅限当前内容”。
- 不提供静默自动写入正文的按钮；素材是否最终使用仍由候选版本和用户确认控制。

## 验证结果

- Evidence 图谱定向后端测试：19 passed。
- 证据撤销和行动重建定向测试：1 passed。
- 后端全量：728 passed，58 warnings；总覆盖率 85.86%。
- 前端定向：2 files、6 passed。
- 前端全量：50 files、331 passed、2 skipped。
- 前端 lint：通过。
- 前端 production build：通过。

## 下一阶段

“观点候选”和“系列关系候选”的显式确认流程已经完成，详见 [CreatorViewpoint 阶段实施记录](./creator-viewpoint-stage-2026-07-20.md) 与 [CreatorSeries 阶段实施记录](./creator-series-stage-2026-07-21.md)。声音模式仍需建立独立证据与确认门，不能把偶然措辞静默推断为长期创作者身份。
