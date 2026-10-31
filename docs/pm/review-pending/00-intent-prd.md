# A0/A1 + A3/A4 一页 · 周复盘「欠对账」全量显示（pilot14，D1）

> 工件：A0/A1 + A3/A4 一页（按 `_sync/p3/lite-matrix-v0.1.md` D1）｜版本 v1 · 2026-10-31｜档位 **T0 / D1**
> 证据等级：E1（代码 + C1 审查记录）
> 决策人：用户（2026-10-31 授权 N1+N2；原文 `_sync/p3/user-authorization-2026-10-31.md`）
> 基线：`origin/main = 2d08a1d`（C1/C2/C3 合并后）
> B-16 语义检查：RG0/RG2 必须附 `_sync/p3/b16-semantic-checklist.md` 逐条判定。

## 1. 问题与证据

- `frontend/src/pages/Review/ReviewPage.tsx:172`：`pending.slice(0, 3).map(...)`——「欠对账」只渲染前 3 条；有第 4 条以上待回填时，用户**看不到、也无法回填**后面的项目。
- C1（PILOT-11）只修了「本周对照」窗口（7 天）与「欠对账」取数（60 天），**没有解决渲染截断**；C1 的 A9-20261031-02 只声明 8–60 天已对照行不展示，未覆盖 pending 截断。
- 影响：复盘完成率/回填率受限于「只能看到 3 条」，长尾待回填项目被隐藏。

## 2. 目标用户与场景

- 已发布多条内容、需要批量回填表现数据做周复盘的创作者。
- 场景：打开 `/review` → 右栏「欠对账」应能看到全部待回填条目（当前 60 天窗口），逐条回填。

## 3. 范围

1. `ReviewPage.tsx`：移除 `pending.slice(0, 3)`，渲染全部 pending（沿用现有行/表单结构，不新增控件）；
2. 测试：4+ 条 pending 全部渲染；0 条/≤3 条行为不变；加载失败仍不渲染半套；
3. `frontend/e2e/async-loop.spec.ts:61` 的旧文案正则更新（去掉已不存在的 `本周期`，保留当前可见文案）——B-10；
4. 不改后端/接口/数据结构。

**非目标**：不改「本周对照」窗口与 8–60 天已对照行策略（A9-02 不变）；不做视觉重设计、不新增筛选/分页控件；不改 30 门/阈值/权威源；不启用 analytics。

## 4. A3/A4 一页（技术）

- **架构/数据流**：`ReviewPage` 用 `listWeekly(60)` 取 pending；只改渲染层 `pending.map`，无新状态/无接口；数据量上限为 60 天发布记录（按现有产品规模 << 100 行）。
- **NFR**：60 行以内列表渲染无性能问题；无网络/存储变化；错误态沿用现有 `error` 分支。
- **威胁/隐私**：无新数据字段、无外部调用；仅展示用户自己的项目标题/判断。
- **回滚**：单文件前端改动，`git revert` + 重新部署上一 commit（见 §7）。
- **RG1 触发判定**：不触及接口（无 API 变更）、数据/迁移（无 schema）、新增依赖（无）、安全面（无认证/隐私变化）、不可逆操作（纯前端渲染）→ **`RG1 not-triggered`**，理由逐类记录；RG2 复核该判定。

## 5. 验收标准（D1）

| # | 标准 | 验证 |
|---|---|---|
| A1 | 4+ 条 pending 全部渲染（第 4、5 条可见；不截断） | 组件测试（mock 5 条 pending） |
| A2 | 0 条 / ≤3 条行为不变 | 现有测试 + 新增断言 |
| A3 | 加载失败仍显示错误、不渲染半套 | 现有失败用例 |
| A4 | E2E 正则不再依赖 `本周期`；当前文案匹配 | 读 `e2e/async-loop.spec.ts` + 本地命令（如可跑） |
| A5 | tsc/eslint/build/vitest 绿 | 命令输出 |
| A6 | diff 仅 `ReviewPage.tsx` + 其测试 + E2E spec；无后端/接口变化 | `git diff --stat` |
| A7 | 部署时 RG3+OG0+A7 完成，含部署→回滚演练记录 | A7/OG0 文档 |

**成功指标**：5 条 pending 渲染 5/5；无新增 UI 控件；构建/测试绿。
**退出标准**：A1–A6 全绿 + RG0/RG2 approve；部署时 A7 完成；未启用 analytics。

## 6. 设计门（RG0 子集 6）

- 不新增界面元素、不改版式：沿用现有 `lumen-row` / `RetroFillForm` 结构，仅移除截断；原型 `docs/design/content-line-prototype.html` 周复盘右栏为「欠对账」列表。
- 若 RG0 认为「显示全部」属新的界面语义，按 A9 记录或回 RG0 r2；本 A0 不自判通过。

## 7. 发布（D4 lite 矩阵）

- `release_trigger = deploy`：N1 需真实生产部署（用户已授权，含回滚演练）。
- 发布步骤按 `docs/deployment.md` §2：`ssh topicai-server` → `cd /opt/topicai` → `git pull --ff-only`（HEAD=目标 commit）→ `docker compose build` → `up -d --force-recreate` → 健康检查。
- **先演练**：部署 N1 → 健康检查 → 回滚到部署前 HEAD → 健康检查 → 再部署 N1；记录 A7/OG0。
- 回滚：`git checkout <部署前 HEAD> && docker compose build && up -d --force-recreate`；不覆盖 `.env`。

## 8. 风险与未知项

| 风险/未知 | 缓解/验证 |
|---|---|
| 长列表影响可读性 | 沿用现有行结构；60 行以内；若用户反馈再议分页（backlog） |
| E2E 未本地跑 | A5 注明；CI 的 Playwright 回归作为证据（PR CI） |
| 部署/回滚未实测 | 用户已授权“先演练”；A7/OG0 记录每一步输出；失败即停 |
| 长尾 pending 可能 >60 天 | 不在本次范围（A9-02/backlog） |
