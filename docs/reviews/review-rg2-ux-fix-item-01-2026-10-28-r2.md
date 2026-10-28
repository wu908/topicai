# RG2 复审报告（r2）· 内容列表 UX 第 1 项

- 原审查：`review-rg2-ux-fix-item-01-2026-10-28.md`（Lead 自审，未发现 blocking）
- **独立审查结果**：commit `2fb050e`，**1 blocking + 5 major + 7 minor**；测试/类型/lint/build 全绿，但业务映射/验收有缺口。
- 本报告：针对独立审查的修复与复验。
- 修复 commit：`3c84a89`（`fix(content): address RG2 review findings`）。
- 结论：**Conditional（B1 + 5 major 已修；待独立复审 + 390px 视觉）**

---

## 一、独立审查的 1 blocking + 5 major

| ID | 问题 | 修复 |
|---|---|---|
| **B1** | 已沉淀行显示「可复盘/去复盘」，不是「已沉淀/查看」；label 只看 `next_action`，不看 status | `rowStepLabel/rowActionLabel` 先判 `rowGroup==='settled'` → 已沉淀/查看；补 settled+manage_observations、settled+run_blind_review 测试 |
| **M1** | 搜索/筛选空态泛化，无关键词/清除/切组；空组组头被过滤 | 搜索空态「没有匹配「xx」」+清除；筛选空态「这一组暂时没有内容，去『想发的』看看」+切组；选中空组保留组头；补测试 |
| **M2** | 已沉淀 >5 条默认折叠未实现 | 已沉淀组默认 5 条 +「查看全部 N 条」/「收起」；补测试 |
| **M3** | 移动端 chips 仍换行、标题单行、action 64px | 新增 `.content-chips` 横向滚动；mobile 标题 2 行 clamp；action 72px；补静态类名/后续视觉 |
| **M4** | action 事件缺 group；view 初始/搜索重复；action 又发 open | action 补 group；view 仅在非 loading/非空列表/切组时发；action 不再发 open；补测试 |
| **M5** | 全局 `.lumen-tag` 移动端覆盖影响其他页 | 改为 `.lumen-row .lumen-tag` |

## 二、Minor 修复

| ID | 处理 |
|---|---|
| m1 orchestrated-only step | 用 `stageOf()` 映射人话步骤；补测试 |
| m2 页头/脚注两个总计 | 删除脚注 `共 N 条`；只保留页头统计 |
| m3 chips a11y | `role="group"` + `aria-pressed` + 列表 `aria-live` |
| m4 行上下 padding 不可点 | `.lumen-row` padding 0，`.row-main` 覆盖上下；action 外边距 |
| m5 测试缺口 | 新增 settled/空态/折叠/搜索清除/filter 切组测试；键盘/视觉仍未覆盖 |
| m6 `create_version` 文案确认 | 在工件 §11.6 记录“暂按写初稿”，待产品确认 |
| m7 CSS 末尾换行 | 已补 |

## 三、复验证据（本轮）

| 检查 | 结果 |
|---|---|
| 目标 4 文件测试 | **4 files / 30 tests passed**（model 17 / row 4 / analytics 1 / content 8） |
| `tsc -b` | 通过 |
| `eslint .` | 通过 |
| `vite build` | 通过（11539 modules） |
| 全量测试 | **64 files / 480 tests passed**（修复后复跑） |
| `git diff --check` | 通过 |

> 测试命令的 PowerShell exit 1 来自 Vite stderr warning；Vitest 汇总 0 failed。

## 四、仍未验证

- **独立复审**：需要 fresh reviewer 再看 `2fb050e..HEAD` 的修复 diff；本报告是 Lead 修复记录，不是独立结论。
- **390px 视觉**：chips 横向滚动、标题 2 行、72px 按钮未跑浏览器/截图/axe。
- **键盘/读屏**：原生 button 行为是推断，未跑 Enter/Space/Tab/axe。
- **覆盖率门**：未跑 `pnpm test` 的 lines 80/functions 66/branches 66/statements 76。
- **后端/HTTP**：settled→next_action 仍基于 SQL + 模型探针，不是真实 DB/API。

## 五、判定

**Conditional**：B1 与 5 major 已修，测试/类型/lint/build 通过；但独立复审和 390px 视觉未完成。通过后更新 pilot-log 为 RG2 approve。
