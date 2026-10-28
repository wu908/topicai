# 第 1 项 · 内容列表（分组 + 行内下一步按钮）

> 状态：**RG0 通过（2026-10-28）**；高保真门已确认；RG1 技术设计已补；**D1 实现完成（commit 2fb050e）**，待 RG2 代码/证据审查。
> 证据等级：**E1/E2**（内部 UX 审计 + 截图；非用户访谈/量化数据）。
> 范围：仅「内容」页的列表视图；不含项目屏、空态入口重构（那些是后续项）。
> 依据：[UX 审计报告](ux-audit-2026-10-21.md) §3.1/§3.2，截图
> `content-empty-state.png`、`content-with-project.png`（本地全量在
> `browser-screenshots/ux-audit-2026-10-21/`）。
> 本次修订只改本工件：补成功指标、决策/kill、风险/回滚、分组边界；未改代码/设计件。
>
> 已确认的三个选择（2026-10-22）：
> 1. 分组命名：**想发的 / 等复盘的 / 已沉淀**
> 2. 行尾按钮：**按下一步给具体动词**（继续 / 去发布 / 回填数据 / 去复盘 / 查看）
> 3. **删除** `意图 1/5`
>
> 产物：
> - 逻辑图（门 1）：[logic.html](ux-fix-item-01/logic.html) ／ [logic.png](ux-fix-item-01/logic.png)
> - 低保真线框（门 2）：[wireframe.html](ux-fix-item-01/wireframe.html) ／ [wireframe.png](ux-fix-item-01/wireframe.png)
> - 高保真可交互（门 3）：[hifi.html](ux-fix-item-01/hifi.html) ／ [hifi-desktop.png](ux-fix-item-01/hifi-desktop.png) ／ [hifi-mobile.png](ux-fix-item-01/hifi-mobile.png)

## 1. 为什么先修这个

零基础用户打开「内容」页，只会问三个问题：

1. **我现在该做哪条？**（优先级）
2. **这条到哪一步了？**（进度）
3. **我点哪里继续？**（动作）

现在的页面三个都答不好：

- 列表是**一锅平铺**的，没有"先做哪条"的分组；
- 行首 `意图 1/5` 是内部阶段，用户读不懂；
- 行里只有文字"下一步：先写下真实经历"，**没有可点的按钮**，整行点击后直接跳项目屏，用户不知道会去哪；
- 顶部统计出现两遍（页头一行 + 筛选 chips 里再一遍）；
- `需要我` 既是行内标签又是筛选，语义混。

这是内容页"不尽人意"的根因之一，所以排第 1 项。

## 2. 目标（做完后用户能怎样）

- 打开内容页 10 秒内知道：有几条要我做、先做哪条、点哪个按钮继续。
- 不进入项目屏也能看清"每条到哪一步、下一步是什么"。
- 列表和项目屏用同一套「下一步」文案，不再各说各话。

### 2.1 可测成功指标（RG0 补齐）

- **主指标（可用性测试）**：5 名目标用户中 **≥4/5** 能在 **10 秒内**正确完成"指出最该先做的一条 + 点击继续/去发布"。
- **辅助指标（上线后埋点）**：内容页行内按钮点击率、内容页→项目屏转化率；上线前采集 **7 天基线**，上线后 **14 天**对比；无基线时记录绝对值与趋势。
- **退出标准**：主指标 **<3/5**，或关键任务完成率下降 **>10%**，或出现 P0/P1 线上问题 → 回滚/重设计。

## 3. 信息架构

### 3.1 分组（推荐 A）

| 分组 | 包含的项目 | 用户理解 | 对应现有数据 |
|---|---|---|---|
| **想发的** | 还没发布、需要你推进 | "我要把它写出来/发出去" | `needsMe(project)`（未发布、非观察中、非已沉淀） |
| **等复盘的** | 已发布、等观察窗口/回填数据 | "发出去了，等数据回来" | `isObserving(project)`（观察中） |
| **已沉淀** | 已复盘完、归档 | "这件事已经结束" | `status === 'settled'` |

> 备选命名：`待我推进 / 观察中 / 已沉淀`。推荐"想发的 / 等复盘的 / 已沉淀"——更像人话，也和"今日"的"想发的"说法一致。**已按 2026-10-22 记录确认采用推荐命名。**

### 3.1.1 状态映射与边界

| 现有状态 | 分组 | 默认按钮 | 边界/fallback |
|---|---|---|---|
| `needsMe(project)` = true | 想发的 | 按 3.4 映射；缺失时 `去处理` | 未发布、非观察中、非已沉淀 |
| `isObserving(project)` = true | 等复盘的 | 回填数据 / 去复盘 / 查看 | 观察窗口内 |
| `status === 'settled'` | 已沉淀 | 查看 | 已复盘归档 |
| 状态未知/空/旧数据 | 想发的 | `去处理` | 记录前端 warning；不阻断渲染 |
| 无 `next_action` | 按状态归组 | `查看` | 不显示空按钮；副行只保留更新时间 |
| 同时满足多个条件 | — | — | 优先级：`settled` > `isObserving` > `needsMe`；只归一组 |

### 3.2 页头与筛选

- 页头副标题：`共 6 条 · 3 条待你推进`（只出现一次总计，不再四个数字）。
- 右侧主按钮：`开始一条`（现"快速开始"）。
- 筛选 chips：`想发的 3` `等复盘的 2` `已沉淀 1`（数量放在 chips 里，页头不重复；`全部` 可省略或放最左）。
- 搜索框移到 chips 同一行右侧（桌面）；移动端单独一行。

### 3.3 行结构（桌面）

```
┌───────────────────────────────────────────────────────────────────────┐
│ [定方向]  租房小空间收纳的 3 个坑                                       │
│           下一步：先补一个真实细节 · 今天 20:21              [继续]   │
└───────────────────────────────────────────────────────────────────────┘
```

- 左：**人话步骤**（取代 `意图 1/5`）：`定方向 / 找素材 / 写初稿 / 发前检查 / 去发布 / 等数据 / 可复盘 / 已沉淀`。
- 主标题：项目标题（最多 1 行，超出省略；后续可换 AI 命名，本项不做）。
- 副行：`下一步：<nextActionLabel>` + `· 更新时间`。
- 右侧：**主按钮**（见 3.4），整行仍可点（键盘 Enter 同效）。
- 不再放 `需要我` 行内 chip（改由分组表达）；如需要，放一个很轻的 `需要你` 点。

### 3.4 行内按钮文案（推荐按下一步动作给具体动词）

| 项目下一步 / 分组 | 按钮文案 |
|---|---|
| 想发的 · 阶段 1–3（定方向/找素材/写初稿） | `继续` |
| 想发的 · `record_publication`（稿好了去发） | `去发布` |
| 想发的 · 其他需处理动作 | `去处理` |
| 等复盘的 · `add_snapshot` / `add_comparable_snapshot` | `回填数据` |
| 等复盘的 · `run_blind_review` / `create_observation` | `去复盘` |
| 等复盘的 · `await_observation_window` | `查看` |
| 已沉淀 | `查看` |

> 备选：统一 `打开`。推荐具体动词——零基础用户不需要再猜"打开之后干嘛"。

### 3.5 排序与筛选

- 「全部」视图：按 `想发的 → 等复盘的 → 已沉淀` 分组；组内按 `updated_at` 倒序。
- 点某个 chip：只显示该组，组头保留。
- 搜索：标题 / 形态 / 下一步文案；无结果给"没有匹配「xx」的内容 + 清除搜索"。
- 已沉淀超过 5 条时默认折叠，给"查看全部 N 条"。

## 4. 状态与空态

| 状态 | 显示 |
|---|---|
| 加载 | 保留现有骨架（3 行），组头占位 |
| 加载失败 | 现有 Alert + 重试，不动 |
| 没有项目 | 本项只做列表区域：主按钮「开始一条」+ 折叠"不知道怎么开始？"（盘点经历 / 贴对标）——空态完整重构排第 2 项 |
| 筛选无结果 | `这一组暂时没有内容，去「想发的」看看` + 一键切组 |
| 搜索无结果 | `没有匹配「关键词」的内容` + 清除 |

## 5. 移动端（390 宽）

- chips 横向滚动，不换行（现在会换 3 行并把"全部内容"断字）。
- 行变为两行：标题 2 行 + 副行 1 行；按钮固定右侧 72px，高 44px（触控）。
- 组头吸顶（可选，先不做也行）。
- 浮动 AI 球移到右下安全区，不遮挡行尾按钮（与列表优化同批处理）。

## 6. 改动落点与工作量（不写代码，仅评估）

| 文件 | 改动 |
|---|---|
| `frontend/src/features/content/projectListModel.ts` | 新增 `groupProjects()`、`rowStepLabel()`、`rowActionLabel()`、`sortProjects()`；复用现有 `needsMe/isObserving/stageOf/nextActionLabel` |
| `frontend/src/features/content/ProjectListRow.tsx` | 左标签换人话步骤；右侧加按钮；去掉 `意图 n/5` |
| `frontend/src/pages/Content/ContentPage.tsx` | 列表按组渲染；统计去重；chips/搜索布局；无结果与折叠 |
| `frontend/src/pages/Content/ContentPage.css` | 组头、行、按钮、chips 横向滚动、移动端 |
| 测试 | `projectListModel.test.ts`（分组/排序/按钮文案）、`ContentPage.test.tsx`（组头/按钮/无结果）、`ProjectListRow.test.tsx`（步骤/按钮/可访问名） |

- API：**不需要改**，`title/status/next_action/updated_at/content_form` 现成。
- 估算：前端 0.5–1 天（含测试），不涉及后端。

### 6.1 风险与回滚

- **风险类**：前端 UI / 可逆；不涉及 API、数据、权限、支付、AI 模型/prompt。
- **影响面**：仅内容页列表；项目屏/抽屉不改；第 2/3 项不扩范围。
- **回滚**：revert 本次 commit；如加 feature flag（`content_list_v2`），关闭开关即可；无数据迁移。
- **监控**：前端错误率、列表行内按钮点击、JS 异常；上线后 24h 观察。
- **已知取舍**：移动端浮动 AI 球隐藏（本项不处理，登记为后续项，不阻塞）。

## 7. 验收标准

- [ ] 列表按「想发的 / 等复盘的 / 已沉淀」分组；组内按更新时间倒序。
- [ ] 每行有可见主按钮，文案按 3.4 映射；点击进入对应项目。
- [ ] 页面不再出现 `意图 1/5`；`需要我` 不再作为行内 chip（或降级为轻点）。
- [ ] 顶部统计只出现一次；chips 数量与分组一致。
- [ ] 搜索/筛选/无结果/折叠都有明确文案。
- [ ] 移动端 chips 不换行、按钮 44px 可点。
- [ ] 文案统一：页头/空态统一为「开始一条」。
- [ ] **可用性测试**：5 名目标用户 ≥4/5 在 10 秒内完成“指出先做哪条 + 点继续/去发布”；<3/5 则回退/重设计。
- [ ] **埋点**：行内按钮点击率、内容页→项目屏转化率可采集；有 7 天基线/14 天对比（或绝对值+趋势）。
- [ ] `pnpm lint`、`pnpm test`、`pnpm build` 全绿。

## 8. 决策记录与待确认

### 8.1 已确认（2026-10-22）

| 决策 | 结论 | 决策人 | 日期 |
|---|---|---|---|
| 分组命名 | 想发的 / 等复盘的 / 已沉淀 | 产品负责人 | 2026-10-22 |
| 行尾按钮 | 按下一步给具体动词（继续/去发布/回填数据/去复盘/查看） | 产品负责人 | 2026-10-22 |
| `意图 1/5` | 直接删除 | 产品负责人 | 2026-10-22 |

### 8.2 高保真门（已确认）

- 高保真原型已出（`hifi.html` / 截图）；**2026-10-28 产品负责人确认**，可进入 RG1/生产实现。

### 8.3 Kill criteria

- 可用性测试 <3/5 或关键任务完成率下降 >10% → 回退/重设计。
- 实现导致既有内容页任务回归（P0/P1）→ 回滚。
- 范围扩展到项目屏/空态重构 → 停止，拆回后续项。

### 8.4 接受的风险

- 移动端浮动 AI 球本项隐藏，待全局移动端修复项处理。
- 抽屉里的项目屏是入口占位（第 3 项单独做）。
- 原型“开始一条”创建条目为前端示例，刷新恢复（原型行为，不接后端）。

## 9. 布局草图（讨论用，不是最终线稿）

```
内容                                          共 6 条 · 3 条待你推进     [开始一条]
[想发的 3] [等复盘的 2] [已沉淀 1]                         [搜索标题或形态]

── 想发的 ───────────────────────────────────────────────────────────
[定方向]  租房小空间收纳的 3 个坑
          下一步：先补一个真实细节 · 今天 20:21                  [继续]
[写初稿]  下班后 10 分钟整理书桌
          下一步：先写下真实经历 · 昨天                            [继续]
[去发布]  第一篇：我为什么开始做自媒体
          下一步：记录已经发布 · 3 天前                            [去发布]

── 等复盘的 ─────────────────────────────────────────────────────────
[等数据]  收纳工具踩坑合集
          下一步：回填实际表现 · 2 天前                            [回填数据]

── 已沉淀 ───────────────────────────────────────────────────────────
[已沉淀]  第一次复盘
          下一步：无 · 10 月 12 日                                 [查看]
```

移动端：

```
内容                             [开始一条]
共 6 条 · 3 条待你推进
[想发的 3] [等复盘的 2] [已沉淀 1]  ← 横向滚动
搜索标题或形态
── 想发的 ─────────────
[定方向] 租房小空间收纳…
下一步：先补一个真实细节
今天 20:21                    [继续]
```

## 10. 高保真可交互原型（门 3，已确认）

- 文件：[hifi.html](ux-fix-item-01/hifi.html)（直接浏览器打开，桌面 + 移动响应式）
- 截图：[hifi-desktop.png](ux-fix-item-01/hifi-desktop.png)、[hifi-mobile.png](ux-fix-item-01/hifi-mobile.png)

已实现的可试交互：

1. **筛选**：全部 / 想发的 / 等复盘的 / 已沉淀，数量实时更新；
2. **搜索**：标题 / 形态 / 下一步，含无结果文案；
3. **折叠**：已沉淀默认折叠，点「展开」查看；
4. **开始一条**：弹出创建面板，输入一句话后新条目落到「想发的」顶部（示例数据）；
5. **点击任意行 / 行尾按钮**：右侧抽屉展示项目入口（项目屏本身留到第 3 项）；
6. **重置示例**：顶部原型条一键恢复。

视觉上沿用了现有 Lumen 设计系统：玻璃侧栏 / 主面板、渐变光场 + 点阵、22px 圆角、墨色胶囊按钮、五档字号；移动端底栏与 chips 横向滚动也按线框落地。

已知取舍：
- 抽屉里的项目屏是入口占位（第 3 项单独做，不在本项偷偷扩范围）；
- 移动端隐藏了浮动 AI 球（当前页面的球会压住行尾按钮，等移动端全局修复项一起处理）；
- 「开始一条」创建的条目是前端示例，刷新即恢复（原型，不接后端）。

## 11. 技术设计（RG1 补齐）

> RG1 发现 4 个接缝；本节只补设计，不改代码。实现时以本节为准。

### 11.1 动作/步骤/按钮映射

`nextActionLabel()` 仍用于详情/副行句子；**列表按钮不复用它**，新增：

- `rowStepLabel(project)`：人话步骤（左标签）
- `rowActionLabel(project)`：按钮动词
- `rowGroup(project)`：`wanted | observing | settled`

| next_action | 人话步骤 | 按钮 | 分组 | 备注 |
|---|---|---|---|---|
| **任意 `status=settled`** | **已沉淀** | **查看** | 已沉淀 | **优先于 next_action**（§3.4） |
| `create_version` | 写初稿 | 继续 | 想发的 | 现有 `stageOf` 为 1；旧数据无 next_action 时也落这里 |
| `lock_hypothesis` | 发前检查 | 继续 | 想发的 | 锁定发布意图 |
| `record_publication` | 去发布 | 去发布 | 想发的 | 稿好了去发 |
| `add_snapshot` | 等数据 | 回填数据 | 等复盘的 | 观察窗口内 |
| `add_comparable_snapshot` | 等数据 | 回填数据 | 等复盘的 | 补充对照 |
| `run_blind_review` | 可复盘 | 去复盘 | 等复盘的 | 观察结束 |
| `create_observation` | 可复盘 | 去复盘 | 等复盘的 | 决定下一次验证 |
| `manage_observations` | 可复盘 | 去复盘 | 等复盘的 | 处理已记录观察 |
| `await_observation_window` | 等数据 | 查看 | 等复盘的 | 等待中 |
| `review_calibration_issue` | 可复盘 | 修正数据 | 等复盘的 | 数据问题 |
| `orchestrated_action` 存在 | 用 `stageOf()` 对应的人话步骤 | 按 `action_type` 映射；未知 → 继续 | 按状态 | **不拿 title 当按钮**；title 只用于副行“下一步” |
| `next_action` 缺失/未知**且无 `orchestrated_action`** | 待处理 | 去处理 | 想发的 | 记录 dev warning；不阻断渲染 |

**`orchestrated_action.action_type` 按钮映射**（`next_action` 缺失时）：

| action_type | 按钮 |
|---|---|
| `record_publication` | 去发布 |
| `add_performance` | 回填数据 |
| `review_result` / `confirm_learning` / `manage_learning` | 去复盘 |
| `await_observation_window` / `scope_learning` | 查看 |
| `review_candidate` / `answer_key_question` / `create_project` / `confirm_intent` / `lock_intent` / `confirm_publish_scope` | 继续（默认） |
| 其他/未知 | 继续 |

> 当前列表 API 的 `next_action` 恒有值，`orchestrated_action` 单独存在的分支不可达；若未来可达，步骤（`rowStepLabel`）与按钮需按同一 `action_type` 再对齐，避免“定方向 + 去发布”这类语义错位。

> 实现新增 `rowStepLabel`/`rowActionLabel` 后，`ProjectListRow` 不再使用 `rowTag`/`progressOf`；`nextActionLabel` 保留给副行。

### 11.2 行结构 / 可访问性（避免嵌套交互）

**DOM 结构（推荐）**：行容器不绑定点击；左侧主体是一个按钮，右侧动作是另一个按钮。

```tsx
<div className="lumen-row" data-testid="project-row" aria-current={selected || undefined}>
  <button type="button" className="row-main" onClick={() => onSelect(id)}
          aria-label={`打开：${project.title}`}>
    <span className="lumen-tag">{rowStepLabel(project)}</span>
    <span className="body">
      <span className="title">{project.title}</span>
      <span className="meta">下一步：{nextActionLabel(project)} · {formatTime(updated_at)}</span>
    </span>
  </button>
  <button type="button" className="row-action" onClick={() => onSelect(id)}
          aria-label={`${rowActionLabel(project)}：${project.title}`}>
    {rowActionLabel(project)}
  </button>
</div>
```

规则：
- **不要** `<div onClick>` 里再放 `<button>`；不要让行容器同时 role=link 又包含 button。
- 键盘：两个原生 button 自带 Enter/Space；焦点顺序 `row-main → row-action`；不额外加 `tabIndex`。
- 若保留“整行空白区域可点”，用 CSS 让 `row-main` 伸展覆盖，不靠行容器 onClick。
- `aria-current` 只标当前选中；动作按钮 `aria-label` 带项目标题，避免“继续”重复不可区分。
- 移动端：`.row-action` 最小 44×44px；`.lumen-row` 允许两行；chips 横向滚动。
- 测试：`getByRole('button', {name: '继续：<title>'})`；断言无嵌套 button；Tab 顺序。

### 11.3 分组 / 排序 / 搜索（修正现有冲突）

- **删除 `waiting`**：现有 `groupByOwner` 的 `waiting` 与 `needs_me` 重叠（`needsMe` 已包含 `next_action === undefined`），不能同时渲染。
- 新函数：
  ```
  groupProjects(projects) -> { wanted, observing, settled }
  ```
  - 优先级：`settled` > `isObserving` > `needsMe`（只归一组）。
  - `needsMe = !settled && !observing`；`next_action` 缺失/未知 → `wanted`。
  - 组内按 `updated_at` 倒序；同时间用 `id` 稳定排序。
- 搜索：haystack 增加 `nextActionLabel`、`rowStepLabel`、`rowActionLabel`（title/形态/下一步都命中）。
- 空结果：保留产品 4 节文案；搜索无结果给「没有匹配「关键词」」+ 清除按钮；筛选无结果给「这一组暂时没有内容，去『想发的』看看」+ 切组按钮；选中空组也保留组头。
- 折叠：已沉淀 >5 条默认显示 5 条 +「查看全部 N 条」/「收起」。
- 测试：`undefined/未知 next_action`、`settled+observing` 冲突、同时间排序、搜索“继续/回填”命中、settled 真实 next_action 文案。

### 11.4 测试与埋点

**测试文件与命令**（按项目现有脚本）：
- `frontend/src/features/content/__tests__/projectListModel.test.ts`：更新旧 `groupByOwner`/`waiting` 断言；新增 `rowStepLabel`/`rowActionLabel` 全 10 个 key + orchestrated + unknown；`groupProjects` 优先级/排序/搜索。
- `frontend/src/features/content/__tests__/ProjectListRow.test.tsx`（**新建**）：两个 button 角色、可访问名、无嵌套 button、键盘 Enter/Space、无重复导航。
- `frontend/src/pages/Content/__tests__/ContentPage.test.tsx`：组头/统计只一次/chips 数量/搜索空态+清除/筛选空态+切组/已沉淀折叠/动作按钮导航/移动端类名（可快照）。
- 命令：`pnpm --dir frontend test`、`pnpm --dir frontend lint`、`pnpm --dir frontend build`（若项目脚本不同，以 `frontend/package.json` 为准）。

**埋点**（用于产品 2.1 辅助指标）：
| 事件 | 触发 | 参数 |
|---|---|---|
| `content_list_view` | 列表真正渲染且非 loading/empty；切换组 | `group`, `count` |
| `content_list_project_open` | 点击行主体/标题（via=title） | `project_id`, `group`, `via=title` |
| `content_list_action_click` | 点击行尾按钮 | `project_id`, `group`, `action`, `next_action` |
- 转化率 = `content_list_project_open / content_list_view`（按 group/窗口）；按钮点击率 = `action_click / view`。
- 搜索不重复发 view；行尾按钮只发 action，不再额外发 open；不采集标题/正文等 PII。

### 11.5 实现顺序

1. `projectListModel`：`rowStepLabel`/`rowActionLabel`/`groupProjects`/搜索；更新测试。
2. `ProjectListRow`：DOM/按钮/可访问名；新建测试。
3. `ContentPage`：组渲染/统计去重/chips/搜索/无结果；更新测试。
4. CSS：桌面/移动、44px、chips 横向滚动、focus 样式。
5. 埋点；跑 lint/test/build；提交 RG2。

### 11.6 决策记录（产品确认）

- `create_version` 左标签：**2026-10-28 暂按“写初稿”实现**（现有 `stageOf` 为 1；确认过的 hifi 样本同时出现“定方向”/“写初稿”，不是唯一映射）。产品若改“定方向”，只改 `rowStepLabels.create_version` 一行，不影响结构。

## 12. 修订记录

- **2026-10-27 RG0 修订**：补可测成功指标/退出标准；补决策记录与 kill criteria；补状态映射边界；补风险/回滚/影响面；统一「开始一条」文案；明确高保真门待确认。未改代码/设计件。
- 关联 RG0 报告：`docs/reviews/review-rg0-ux-fix-item-01-2026-10-27.md`（旧 hash 的 Conditional 结论，本次修订后需按新 hash 复审）。
- **2026-10-28 RG0 通过**：产品负责人确认高保真门；RG0 通过，进入 RG1。
- **2026-10-28 RG1 技术设计**：补 11.1 动作/步骤/按钮映射、11.2 行结构/可访问性、11.3 分组/排序/搜索、11.4 测试与埋点、11.5 实现顺序；未改代码。
- **2026-10-28 D1 实现**：commit `2fb050e`；model/row/page/CSS/埋点/测试完成；待 RG2。
- **2026-10-28 RG2 独立审查修复**：settled 标签优先、空态/折叠/移动端、埋点 group/view、CSS 作用域；见复审报告。
