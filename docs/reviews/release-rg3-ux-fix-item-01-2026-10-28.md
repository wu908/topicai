# RG3 发布证据 · UX-01 内容列表分组/行操作

- 日期：2026-10-28
- 分支：`pilot/review-flow-2026-10-28`
- 基点：`83f074a`
- 当前 HEAD：`1b7ae01`
- 状态：**Ready for RG3 human sign-off（待发布负责人签字）**
- 变更性质：前端展示/交互 + 埋点；**无后端、无接口、无 schema、无迁移、无依赖变更**

---

## 1. 发布范围

**包含**
- 内容列表三组：想发的 / 等复盘的 / 已沉淀
- 行主体 + 行尾动作两个原生 button；已沉淀行固定「已沉淀 / 查看」
- 搜索/筛选空态：关键词 + 清除；空组切「想发的」
- 已沉淀 >5 条折叠
- 移动端：chips 横向滚动、标题 2 行、action 72×44
- 埋点：`content_list_view` / `project_open` / `action_click`；action 带 group；搜索不重复 view
- 测试：model / row / analytics / page

**不包含**
- 后端 API / DB / migration
- 新依赖 / 新基础设施
- 运营流、发布自动化、Context7

---

## 2. 代码变更

| 文件 | 变更 |
|---|---|
| `frontend/src/features/content/projectListModel.ts` | 分组/排序/搜索；`rowStepLabel` / `rowActionLabel`；orchestrated `action_type` 映射 |
| `frontend/src/features/content/ProjectListRow.tsx` | 两个原生 button；无嵌套交互；action 埋点 |
| `frontend/src/features/content/contentListAnalytics.ts` | 事件 payload（含 group）；无 PII |
| `frontend/src/pages/Content/ContentPage.tsx` | 分组渲染、搜索/空态/折叠、chips、埋点 view 守卫 |
| `frontend/src/pages/Content/ContentPage.css` | chips/折叠/空态样式 |
| `frontend/src/styles/lumen-ui.css` | 行按钮、移动端标题/动作/tag 作用域 |
| 4 个测试文件 | 模型/行/埋点/页面覆盖 |

提交链：

```
2fb050e feat(content): group list and add row actions
edac7f6 docs: rg2 evidence and gate log
3c84a89 fix(content): address RG2 review findings
aebbbd0 docs: record RG2 fix commit
922a5b2 fix: close RG2 re-review newline and record verdict
db54876 docs: close RG2 with visual, keyboard and coverage evidence
69acadf fix(content): map orchestrated action types to row button verbs
efc565f docs: record action mapping verification
1b7ae01 test(content): cover all default action types; close RG2
```

---

## 3. 验证证据

| 检查 | 命令/方式 | 结果 |
|---|---|---|
| 全量测试 | `vitest run --coverage` | **64 files / 482 tests passed**（0 failed） |
| 目标 RG2 测试 | 4 files | **32 tests passed** |
| 覆盖率 | Vitest v8 | All files：lines **82.34** / functions **73.65** / branches **76.39** / statements **84.19**；阈值 80/66/66/76 全过 |
| 类型 | `tsc -b` | 通过（无输出） |
| Lint | `eslint .` | 通过（无输出） |
| 构建 | `vite build` | 通过，11,539 modules；`dist/index.html` SHA256 `298A3281…1E60E`（gitignored） |
| 代码 whitespace | `git diff --check 83f074a..HEAD -- frontend/src` | 通过 |
| 依赖变更 | `git diff --name-only` package/lock/requirements | **无** |
| 后端变更 | `git diff --name-only` backend | **无** |
| 390px 视觉 | Playwright 390×844 | chips `nowrap`，`scrollWidth 286 > clientWidth 259`；标题 2 行；action **72×44** |
| 桌面视觉 | Playwright 1440×900 | 标题单行 ellipsis；action 72×44 |
| 键盘 | `row-main` Enter / `row-action` Space | 均导航到 `/content/{id}` |

截图：
- [390px](visual-rg2-content-390.png)
- [1440px](visual-rg2-content-1440.png)

RG2 报告：[review-rg2-ux-fix-item-01-2026-10-28-r2.md](review-rg2-ux-fix-item-01-2026-10-28-r2.md)（第三轮独立复审 **approve**）

---

## 4. 风险与影响

| 风险 | 等级 | 说明 / 缓解 |
|---|---|---|
| 前端展示回归 | 中 | 已覆盖分组/空态/折叠/移动端；截图 + 482 tests |
| 埋点口径变化 | 中 | `content_list_view` 只在非 loading/非空/切组时发；action 带 group；上线后看 1–2 天事件量，异常回滚 |
| 移动端布局 | 低 | 390px 实测 chips/标题/按钮；未跑真机 |
| 后端/数据 | **无** | 无 API/schema/migration 变更 |
| 依赖/供应链 | **无** | 无新增依赖 |
| 可访问性 | 低 | 原生 button + aria-label；未跑 axe 全量 |
| 浏览器兼容 | 低 | 使用现有 CSS/React 栈；未跑多浏览器矩阵 |

---

## 5. 回滚方案

- **未合并前**：不合并该分支即可；原项目 `G:\codex_project\topicAI\mvp` 代码未动。
- **已合并/已部署**：
  1. 回退到 `83f074a` 的前端构建，或
  2. `git revert --no-commit 2fb050e^..1b7ae01` 后重新构建（保留历史）。
- **无数据库迁移**，不需要数据回滚；无 feature flag，回滚 = 重新部署上一版。
- 埋点异常：前端回滚后事件自然停止；已发事件不删除，分析时按时间窗截断。

---

## 6. RG3 签字

| 项 | 结论 |
|---|---|
| 自动化验证 | ✅ 全绿 |
| 视觉/键盘 | ✅ 已验 |
| 后端/数据风险 | ✅ 无 |
| 回滚可执行 | ✅ 有 |
| **发布负责人** | **待签字：可以合并 / 可以发布 / 暂不** |

> 未签字前不合并、不发布。

---

## 7. 剩余非阻塞

- axe 全量可访问性扫描未跑；基础 aria 已覆盖。
- 覆盖率命令在 PowerShell 包装下显示 exit 1（Vite stderr），Vitest 0 failed、无 threshold error；CI 需确认原生 exit。
- 未做真实后端 HTTP 集成测试；本次无后端变更。
- 埋点上线后需看 1–2 天数据，确认 view/action 口径。

---

## 8. 关联工件

- 产品/设计：[ux-fix-item-01-content-list.md](ux-fix-item-01-content-list.md)
- RG0：[review-rg0-ux-fix-item-01-2026-10-27-r2.md](review-rg0-ux-fix-item-01-2026-10-27-r2.md)
- RG1：[review-rg1-ux-fix-item-01-2026-10-28.md](review-rg1-ux-fix-item-01-2026-10-28.md)
- RG2：[review-rg2-ux-fix-item-01-2026-10-28-r2.md](review-rg2-ux-fix-item-01-2026-10-28-r2.md)
- 门记录：[pilot-log.csv](pilot-log.csv)
- 计划：[2026-10-28-content-list-ux.md](../superpowers/plans/2026-10-28-content-list-ux.md)
