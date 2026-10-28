# RG2 代码/变更审查 · 内容列表 UX 第 1 项

- 审查门：**RG2 变更就绪**
- 变更：commit `2fb050e`（`feat(content): group list and add row actions`）
- 依据：`docs/reviews/ux-fix-item-01-content-list.md` §11（RG1 技术设计）
- 审查者：Lead 自审（独立 reviewer 已发起，待返回；本报告先记录自动化证据与自审结论）
- 结论：**Conditional（无 blocking；待独立 reviewer + 移动端视觉确认）**

---

## 一、变更范围

```
frontend/src/features/content/projectListModel.ts       +112/-?
frontend/src/features/content/ProjectListRow.tsx        +74/-?
frontend/src/features/content/contentListAnalytics.ts   +48 new
frontend/src/pages/Content/ContentPage.tsx              +75/-?
frontend/src/pages/Content/ContentPage.css              +20
frontend/src/styles/lumen-ui.css                        +67
tests: projectListModel / ProjectListRow / contentListAnalytics / ContentPage
```

---

## 二、自动化证据

| 检查 | 命令 | 结果 |
|---|---|---|
| TypeScript | `.\node_modules\.bin\tsc.CMD -b` | 通过（无输出） |
| ESLint | `.\node_modules\.bin\eslint.CMD .` | 通过（无输出） |
| 构建 | `.\node_modules\.bin\vite.CMD build` | 通过（11539 modules；ContentPage chunk 52.26 kB） |
| 全量测试 | `.\node_modules\.bin\vitest.CMD run --coverage=false` | **64 files / 474 tests passed** |
| diff 检查 | `git diff --check` | 通过 |

> 测试命令的 PowerShell 退出码因 Vite/stderr warning 显示 1，但 Vitest 汇总为 0 failed；以输出为准。

---

## 三、自审 findings

### 无 blocking

- 映射：`rowStepLabel`/`rowActionLabel` 覆盖 10 个 `NextAction`；unknown → 待处理/去处理；`nextActionLabel` 保留给副行。
- 分组：`groupProjects` 三组；`waiting` 已删除；`settled > observing > needsMe`；稳定排序。
- 行：无嵌套 button；两个原生 button；`aria-label` 区分；无双重导航。
- 页面：组头/统计只一次/chips/搜索无结果/空组；埋点挂载。
- 测试：模型 15、行 4、埋点 1、内容页 4；全量 474 通过。

### Major（待独立 reviewer 确认）

1. **移动端视觉未实测**：CSS 已加 44px/横向滚动，但未在 390 宽浏览器截图验证（RG3/QA 需补）。
2. **`trackContentListView` 初始会记一次 count=0，加载后再记一次**：埋点噪声；建议 `if (loading) return` 或只在列表渲染后发。非阻塞。
3. **`lock_hypothesis` 左标签“发前检查”仍待产品确认**：§11.6 只确认了 `create_version`；`lock_hypothesis` 可能应为“找素材/发前检查”。不影响结构，但属于产品文案。

### Minor

- 空组不渲染组头（当前只渲染有内容的组）；产品 3.1 说“组头保留”，若要求空组也显示，需调整。
- `ContentPage` 的 counts 仍用逐项 `viewProjects([p])`，O(n²) 风格；列表小，非阻塞。
- 旧 `progressOf` 仍被 `ProjectDetailPane` 使用，未受影响。

---

## 四、独立审查状态

已发起独立 reviewer（fresh context）审查同一 diff；结果未返回。  
在独立 reviewer 返回前，**不能把 RG2 标为 approve**；但自动化证据与自审无 blocking。

---

## 五、判定

**Conditional**：
- 代码/测试/构建通过；无 blocking。
- 待：独立 reviewer 结论 + 390px 视觉截图。
- 通过后进入 RG3（发布证据）或先补 QA 截图。

---

## 六、下一步

1. 收独立 reviewer 结果；有 blocking 则修。
2. 跑 390px 视觉检查（Playwright/浏览器截图）。
3. 补 RG3 发布证据：测试输出、构建、截图、回滚说明。
4. 通过后更新 pilot-log：RG2 approve；记录周期/误杀/漏放。
