# TopicAI Handoff - 2026-08-08 (前端审计 medium 修复轮)

> 本文档由 AI 辅助整理，依据实测结果校对；未记录密钥、令牌或本地敏感配置。

工作区：`G:\codex_project\topicAI\mvp`（**git 仓库根是 `mvp/`，不是 `topicAI/`**）

当前分支：`008-content-project-mvp-completion`

前序交接：`topicai-handoff-2026-08-08-frontend-bug-high-fixes.md`（critical/security/bug-high 三轮）。

## 当前状态

本轮处理前端审计会话 **`e54a2643`** 剩余的 **234 条 medium**（121 low 按约定不处理）。
triage 明细：`backend\.ci-tmp\frontend-medium-triage.md`（逐条原文+定性）与
`backend\.ci-tmp\frontend-medium-comments.json`（原始导出）。

**所有改动尚未提交**（含此前各轮），具体以 `git status --porcelain` / `git diff` 为准。

验证基线（本轮结束时实测）：
- 前端：`vitest run` **211 passed / 32 files**（较 bug-high 轮 168 passed 新增 43 测试），
  `tsc -b` exit 0，`eslint src` exit 0
- 后端：本轮未动，沿用 354 passed / ruff clean 基线

测试命令（PowerShell 执行策略拦截 npx.ps1，直接调 node）：

```powershell
cd G:\codex_project\topicAI\mvp\frontend
node node_modules\vitest\vitest.mjs run
node node_modules\typescript\bin\tsc -b
node node_modules\eslint\bin\eslint.js src
```

## 批次总览

| 批次 | 范围 | 方式 |
|---|---|---|
| D1 | `utils/error.ts` 4 项：数组 detail 拼接、空串消息、原始字符串抛出 | TDD |
| D2 | auth 链一致性：authStore、App 门控、404 路由 | TDD |
| D3 | client.ts / v2client 单例、starter URL 编码、types 契约硬化 | TDD |
| D4 | 内容工作区组件：StageForms / ContentPage / 面板群 / projectDraft | TDD |
| D5 | 杂项组件（EmptyState/ErrorBoundary/LoadingFallback/Sidebar）+ 6 页面 | TDD |
| E | CSS / token / theme 视觉与可访问性修复 | 无测试，全套验证 |

D5 六页面要点（MePage / MaterialsPage / GrowthOnboardingPage / StarterPage /
HomePage / OpportunitiesPage）：

- 幂等键稳定化统一落地（Starter ×4 操作、Opportunities ×3 操作）：
  `keyRef` 存 `{ signature, key }`，失败重试复用同键供服务端去重，载荷变化/成功后轮换
- 请求令牌守卫（requestTokenRef 递增 + 卸载置 -1）覆盖各页 load/run/refresh，
  防卸载后 setState 与乱序响应
- MePage：rate `?? 0`、load 置 loading、打开删除确认框清空残留输入、确认文案常量化
- MaterialsPage：空文件拒绝上传、缺文件提示、pending 期即清错误、size `?? 0`
- GrowthOnboardingPage：attributes 全链路可选守卫、未知 status 回退「暂定」、splitValues 限 5 条
- StarterPage：`loading && !workspace` 才显示全屏 spinner（刷新不卸载表单）

## 批次 E 明细（CSS/token/theme）

| 文件 | 修改 |
|---|---|
| `styles/tokens.css` | decision 调色板改 semantic token 别名防漂移；motion token 加 reduced-motion 覆盖；新增 `--v3-border-hover`/`--v3-surface-hover`/`--v3-sidebar-bg`；`--v3-red-bg` 透明度 0.05→0.08 |
| `styles/globals.css` | `html font-size: 100%`（尊重浏览器字号）；`body overflow-x: hidden` → `html, body overflow-x: clip`（不建滚动容器、不破坏 sticky）；移动端侧栏背景 token 化；侧栏 nav `repeat(5, …)` → `grid-auto-flow: column`（不硬编码项数）；reduced-motion 补 delay/iteration-count/scroll-behavior |
| `styles/theme.ts` | `v3()` 约束为 `V3Token` 联合类型（拼错编译期报错）+ 可选 fallback；Button/Card `transition: all` 收窄为具体属性；caption 颜色 text-ter→text-sec（#9b9b9b 对比度 ≈2.8:1 不满足 WCAG AA） |
| `pages/Home/HomePage.css` | `.today-state-row` 移出共享 flex 规则（与 MUI Stack 内联样式打架）；补缺失的 `.today-action-outcome` / `.today-reject-form` 样式 |
| `pages/GrowthOnboarding/GrowthOnboardingPage.css` | `:first-of-type` → 相邻选择器（section 与 Button/Alert 混排时语义脆弱）；form grid 改 `auto-fit minmax(min(220px,100%),1fr)` 防溢出；`growth-back` 类名加倍去 `!important` |
| `pages/Content/ContentPage.css` | hover 色 token 化（含 `.content-project-row`）；建议面板背景 → `--v3-panel-bg`；`input` 选择器排除 checkbox/radio；`grid-row: 1/span 3` → `1/-1`；candidate 输入控件补 `:focus-visible`；viewpoint/series 重复按钮规则合并 |
| `pages/Starter/StarterPage.css` | hover 边框 `#b8b4ae` → `--v3-border-hover` |
| `pages/Operations.css` | 移动端规则兼容 `> a`；`.operations-meta` 颜色 text-ter→text-sec（对比度） |

## 已关闭 / 留待后续

关闭（误报或已满足）：
- Operations.css「孤儿样式」误报 — 实际被 OpportunitiesPage / MaterialsPage 引用
- tokens.css 暗色 no-op 注释块 — 已有 reserved 注释，暗色主题落地时再填

留待后续（triage 报告有逐条原文）：
- `globals.css` 全局 MUI `!important` 覆盖 — 移除回归风险高，需视觉 QA 配合
- `ContentPage.css` 按 MUI 内部类名隐藏内容（`.MuiTypography-h5` 等）— 需组件侧改造
- `theme.ts` PALETTE 与 tokens.css 重复 — MUI createPalette 不支持 var()，保留注释说明
- tokens.css v3/legacy 双命名空间与二次 `:root` 合并 — 大重构，低收益
- HomePage.css 裸元素选择器（maintainability）、121 条 low、部分纯 maintainability 项

## 复现扫描结果

```bash
cd G:/codex_project/topicAI/mvp
ocr session show e54a2643
ocr session comments --severity medium --json e54a2643
```
