# TopicAI Handoff - 2026-08-08 (前端审计 bug-high 修复轮)

> 本文档由 AI 辅助整理，依据实测结果校对；未记录密钥、令牌或本地敏感配置。

工作区：`G:\codex_project\topicAI\mvp`（**git 仓库根是 `mvp/`，不是 `topicAI/`**）

当前分支：`008-content-project-mvp-completion`

当前 HEAD：`d9a6df9` — `fix: wait for profile refresh before showing import completion`

## 当前状态

本轮是 2026-08-07 交接（`topicai-handoff-2026-08-07-full-repo-scan-backend-hardening.md`）的延续：
后端加固完成后，补做了前端全量扫描（ocr 会话 **`e54a2643`**，46 文件 / 446 评论，
2 critical / 89 high），并完成 critical、security、bug-high 三轮修复。

**所有改动尚未提交**（含后端轮遗留），具体以 `git status --porcelain` / `git diff` 为准。

验证基线（本轮结束时实测）：
- 后端：`pytest` **354 passed**，`ruff check` clean（后端轮结束时基线，本轮未再动后端）
- 前端：`vitest run` **168 passed / 29 files**，`tsc -b` exit 0，`eslint src` exit 0

测试命令（PowerShell 执行策略拦截 npx.ps1，直接调 node）：

```powershell
cd G:\codex_project\topicAI\mvp\frontend
node node_modules\vitest\vitest.mjs run
node node_modules\typescript\bin\tsc -b
node node_modules\eslint\bin\eslint.js src
```

## 前端审计处置总览

扫描结果与定性记录：`backend\.ci-tmp\frontend-bug-high-triage.md`（80 条 bug-high 去重后的定性）。

| 轮次 | 范围 | 状态 |
|---|---|---|
| critical ×2 | client.ts 401 refresh 竞态；ProjectWorkspace 基线版本切换失同步 | 已修（早前） |
| security ×2 | projects.ts URL 参数编码；用户提交 URL scheme 白名单 | 已修（早前） |
| bug-high 批次 A | client/auth 链：204/空体解析、refresh 绕过共享 client 并校验载荷、login/register 响应 shape 校验、LoginPage minLength 仅注册态、删除无后端的 rememberMe | 已修 |
| bug-high 批次 B | 数字 NaN 防御（MePage/StarterPage/StageForms）+ 幂等键稳定化（Materials/GrowthOnboarding，失败重试复用同键，成功后轮换） | 已修 |
| bug-high 批次 C | 状态同步 / dead-end / 防御渲染，10 项（见下） | 已修 |

所有修复均先写失败测试（RED）再实现（GREEN），新测试文件：
`audit-batch5-client-auth.test.tsx`、`projectDraft.test.ts`，其余追加在既有测试文件中。

## 批次 C 明细（本轮新增）

| # | 问题 | 文件 |
|---|---|---|
| 1 | 草稿存储键裸拼接有碰撞（':' 歧义、'no-version' 哨兵撞车）→ 分段 encodeURIComponent + `n`/`v` 前缀 | `features/content/projectDraft.ts` |
| 2 | 非 user_source 机会带 required_action 时只有警告 Alert 无操作控件（dead-end）→ 核验表单对所有机会类型开放；required_action 用真值判断 | `pages/Opportunities/OpportunitiesPage.tsx` |
| 3 | projectId 切换时旧工作台短暂残留 → 渲染期 prevProjectId 重置（规避 set-state-in-effect） | `pages/Content/ContentPage.tsx` |
| 4 | startAction 与 actionPath 对 create_project 解析出不同目的地 → 统一 resolveActionPath；defer/reject 成功后静默刷新；`last_event.payload?.reason` 防御 | `pages/Home/HomePage.tsx` |
| 5 | selectedIds 只挂载时播种，新到达项目永不选中 → seen 集合 + effect 只自动选新增、保留用户取消；drafts/opportunityDrafts updater 改从 prev state 合并 | `features/content/SeriesPanel.tsx` |
| 6 | `rule.versions` / `source_observation_ids` 缺失时列表渲染崩溃 → `?? []` 兜底 | `features/content/ObservationList.tsx` |
| 7 | `review.comparison` 缺失时复盘区块崩溃 → `comparison?.… ?? []` | `features/content/ReviewSummary.tsx` |
| 8 | confirmed_statement 为空时已确认观点渲染空白 → 回退 proposed_statement | `features/content/ViewpointPanel.tsx` |
| 9 | PublicationForm gate 只在挂载时初始化，action 切换后沿用旧 gate → 渲染期 prevActionId 重置 | `features/content/StageForms.tsx` |
| 10 | 存在恢复草稿时自动保存整体禁用（新编辑不落盘）→ 继续写入、仅跳过清理；saveVersion 包 try/catch 保留草稿 | `features/content/ProjectWorkspace.tsx` |

验证期顺带修复的两处编译/lint 问题：
- `MePage.tsx`：lib 的 `Number.isInteger` 不是类型守卫，改局部 `isWholeGoal` 守卫收窄 `number | null`
- `ContentPage.tsx`：effect 内直接 setState 触发 `react-hooks/set-state-in-effect`，改渲染期重置模式

## 尚未处理（留待后续轮次）

- 审计剩余 **234 medium + 121 low** 未定性
- bug-high 边缘项：MePage 导出 gate 流程、GrowthOnboarding version 兜底与 JSON/CSV 解析细节、CSS 可访问性类、types 契约类若干（triage 报告有逐条定性）
- 所有改动未提交；提交需用户明确要求并显式列文件

## 复现扫描结果

```bash
cd G:/codex_project/topicAI/mvp
ocr session show e54a2643
ocr session comments --severity critical,high --json e54a2643
```
