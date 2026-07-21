# TopicAI 系列延展机会阶段实施记录

## 阶段目标

让已确认系列真正减少“下一篇写什么”的决策成本，同时守住用户确认边界：AI 只能准备一个可解释、可编辑的下一篇机会，用户接受前不得创建 ContentProject。

## 冻结契约

- 通用实体为 `ContentOpportunity`，首个类型仅开放 `series_extension`。
- 机会继承已确认系列的 `content_intent` 与 `content_format`。
- 候选包含标题、读者变化、理由、所需素材、证据引用、未知和限制。
- 状态仅为 `proposed -> accepted | rejected`。
- 接受是可逆建项动作，不自动生成正文、不自动排期、不自动发布。
- 同一系列只能有一个待确认机会；已接受机会对应项目发布前，不再准备下一篇。
- 系列来源失效、撤销或版本冲突时不能创建新机会。

## AI 与用户职责

AI 读取用户确认的系列、可复用 Evidence 和已确认观点，准备唯一候选并写入 AITrace。模型不可用时直接使用用户已确认的系列延展方向，不猜测共同主题或外部事实。

用户可以修改标题、读者变化和素材要求，再选择“确认并创建项目”或“这篇不合适”。只有接受事件提交后，系统才使用固定幂等键创建项目，并把继承的内容意图标记为已确认。

## 数据与接口

迁移 `027_content_opportunities.sql` 新增：

```text
content_opportunities
content_opportunity_events
```

接口：

```text
GET  /api/v2/content-opportunities
POST /api/v2/creator-series/{series_id}/extension-opportunities
POST /api/v2/content-opportunities/{opportunity_id}:decide
```

接受后建项位于事务后可重试区。若机会决策已经提交但建项或关联回写中断，同一幂等请求会复用 `opportunity-project:{opportunity_id}`，恢复同一个项目，不会重复建项。决策重放同时校验 `opportunity_id`，避免跨机会误命中。

## 前端行为

现有内容工作台的“内容系列”区增加：

- 已确认系列的“准备下一篇”；
- 尚未建项的可编辑机会；
- “确认并创建项目”与拒绝动作；
- 建项后的“打开下一篇项目”。

旧系列调用方未提供机会回调时，原系列发现、确认和撤销功能保持可用。

## 验证结果

- 迁移、完整表集合和系列机会服务联合：33 passed。
- 系列机会 API 与服务：9 passed。
- 前端系列工作台：9 passed。
- 后端非递归全量：737 passed。
- 前端全量：50 files、338 passed、2 skipped。
- 前端 TypeScript production build：通过。
- 前端 lint：通过。

## 未进入本阶段

- 不建设完整机会列表页和热点机会。
- 不自动创建第二个延展项目。
- 不自动把新项目加入系列；新项目发布后仍需用户确认系列关系。
- 不生成正文、封面、发布时间或发布动作。
- 不把一次机会接受写入长期创作者经验。

## 下一阶段建议

下一阶段把 `ContentOpportunity` 接入“今日”的唯一 NextBestAction：只有当前没有临近发布、待确认或待复盘任务时，才把系列延展机会作为主动作。这样机会会进入 AI 编排，而不是继续停留在项目页中的可选按钮。
