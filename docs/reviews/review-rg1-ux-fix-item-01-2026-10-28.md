# RG1 技术就绪审查报告 · 内容列表 UX 第 1 项

- 审查门：**RG1 技术就绪**
- 审查对象：`docs/reviews/ux-fix-item-01-content-list.md`（hash `DC7C71760EF09F9E…`，15,203 B）
- 设计工件：`logic.candidate.json` / `logic.html` / `wireframe.html` / `hifi.html`（已确认）
- 代码基线：`frontend/src/features/content/{projectListModel.ts,ProjectListRow.tsx}`、`frontend/src/pages/Content/{ContentPage.tsx,ContentPage.css}`、相关 `__tests__`
- 审查日期：2026-10-28
- 档位判断：**D1**（多文件、前端 UI、可逆、无 API/数据/权限变化）
- RG1 规则：D1 为**咨询**，不强制阻断；但以下 4 项建议在开工前补齐，否则 RG2 会退回。
- 结论：**Advisory Conditional（建议补齐后开工）**

---

## 一、结论

产品工件已通过 RG0；技术上可行，但现有代码与目标设计之间还有 **4 个未定义的接缝**：

1. **动作/步骤映射不完整**：`NextAction` 有 10 个，产品表只覆盖部分；`nextActionLabel` 可能返回 `orchestrated_action.title`（一句话，不是按钮动词）。
2. **行交互/可访问性未设计**：当前行是 `<div onClick>`，没有 role/tabIndex/键盘；直接加按钮会形成嵌套交互元素。
3. **分组算法与现有 `groupByOwner` 冲突**：`waiting` 与 `needs_me` 重叠，产品只要 3 组。
4. **测试/埋点计划与现状不符**：`ProjectListRow.test.tsx` 不存在；`ContentPage.test.tsx` 只有 3 个基础用例；成功指标埋点未定义。

---

## 二、代码级发现

### RG1-1（Must-fix）动作/步骤映射不完整

- 证据：
  - `projectListModel.ts` 第 9–20 行：`nextActionLabels` 覆盖 10 个 `NextAction`。
  - 第 27–31 行：`nextActionLabel()` 优先返回 `orchestrated_action.title`（如“确认候选内容是否准确表达了你”），不是按钮动词。
  - 产品工件 3.4 只列了部分动作；`manage_observations`、`review_calibration_issue`、`orchestrated_action` 的按钮/人话步骤未定义。
  - `stageOf` 第 39–58 行默认回 `1`；8 个人话步骤与 10 个动作的映射未完整。
- 风险：实现者会猜；列表/工作台文案再次漂移；未知动作显示错误按钮。
- 要求：补一张完整映射表（`NextAction` + `orchestrated_action` + unknown/undefined → 人话步骤 + 按钮动词 + fallback），并覆盖全部 key 的测试。建议新增 `rowStepLabel()` / `rowActionLabel()`，不要让按钮复用 `nextActionLabel()` 的句子。

### RG1-2（Must-fix）行交互/可访问性未设计

- 证据：
  - `ProjectListRow.tsx` 第 53–60 行：`<div onClick>`，无 `role`、`tabIndex`、`onKeyDown`。
  - 产品工件 3.3 要求“整行仍可点（键盘 Enter 同效）”，当前代码不满足。
  - 若直接在行内加 `<button>`，会形成 **button inside clickable div** 的嵌套交互问题；点击按钮可能冒泡触发两次导航。
- 要求：明确结构（推荐：行容器不绑定点击；标题用链接/按钮，右侧独立动作按钮；或行用 `role="link"` + 键盘处理，按钮 `stopPropagation`），并补可访问名/焦点顺序测试。

### RG1-3（Must-fix）分组算法与现有 `groupByOwner` 冲突

- 证据：
  - `projectListModel.ts` 第 91–103 行：`groupByOwner` 同时返回 `needs_me` 和 `waiting`。
  - 第 34–36 行：`needsMe = !done && !observing`，所以 `waiting`（`next_action === undefined`）也属于 `needs_me`。
  - 产品要 3 组（想发的 / 等复盘的 / 已沉淀），没有 `waiting`。
- 风险：若直接渲染 `groupByOwner`，同一条会出现两次；未知/无下一步状态归属不清。
- 要求：删除/合并 `waiting`；定义优先级 `settled > observing > needsMe`；unknown/undefined → 想发的 + `去处理`；补边界测试。

### RG1-4（Must-fix）测试/埋点计划与现状不符

- 证据：
  - 产品工件第 142 行列 `ProjectListRow.test.tsx`，但该文件不存在；测试在 `__tests__/` 下。
  - `projectListModel.test.ts` 仍断言 `groupByOwner` 的 `waiting` 行为（第 152–163 行），改分组后会失败。
  - `ContentPage.test.tsx` 只有骨架/项目屏/列表 3 个用例（第 150–174 行），没有分组/按钮/无结果/可访问性。
  - 产品成功指标的“行内按钮点击率/内容页→项目屏转化率”没有事件名/上报位置。
- 要求：更新/新增测试（分组、排序、按钮映射、无 next_action、未知状态、键盘、44px、无结果）；定义埋点事件（名称/参数/触发点）；在 RG2 前给出测试命令与预期输出。

---

## 三、其他风险（Major/Minor）

| ID | 级别 | 问题 | 建议 |
|---|---|---|---|
| RG1-5 | Major | 搜索 `searchProjects` 只搜 title/intent/content_form（第 119–125 行），产品要求“标题/形态/下一步” | 把 `nextActionLabel`/人话步骤加入 haystack；补测试 |
| RG1-6 | Major | 页头统计与 chips 重复（`ContentPage.tsx` 260–262 + 303–313） | 按产品 3.2 只留一行总计 + chips 数量；补快照/断言 |
| RG1-7 | Major | 当前行标签用 `意图 n/5`（`rowTag` 第 29–33 行），产品要求删除 | 换人话步骤；确认与工作台文案同源 |
| RG1-8 | Minor | `ContentPage` counts 用 `viewProjects([p], ...)` 逐项过滤，O(n²) 风格 | 用一次 group/filter 计算；列表小，非阻塞 |
| RG1-9 | Minor | 无 feature flag/回滚实现细节 | 可 revert commit；如需灰度，加 `content_list_v2` 开关（可选） |
| RG1-10 | Minor | 移动端 44px/横向滚动只在产品描述，CSS 未验证 | 实现后 Playwright/截图验证；补 `ProjectListRow` 可访问名 |

---

## 四、RG1 判定

- **D1 档：RG1 为咨询，不阻断开工。**
- 但 **RG1-1/2/3/4 建议在写代码前补齐**，否则 RG2 会以“映射/交互/分组/测试未定义”退回。
- 补齐方式：在 `docs/reviews/ux-fix-item-01-content-list.md` 增加“技术设计”小节（映射表、行结构、分组算法、测试/埋点），或单独 `docs/reviews/ux-fix-item-01-tech-design.md`；不需要改代码。
- 补齐后可直接进入 D1 实现；RG2 审查代码/测试/证据，RG3 发布证据。

---

## 五、Gate 记录

| 项 | 值 |
|---|---|
| 门 | RG1（D1 咨询） |
| 产品工件 hash | `DC7C71760EF09F9E…` |
| 结论 | Advisory Conditional |
| Must-fix | 4（映射/交互/分组/测试埋点） |
| 是否改代码 | 否 |
| 下一步 | 补技术设计 4 项 → D1 实现 → RG2 |

> 本次仅新增审查报告；未改产品工件/设计件/代码。
