# A5 · 测试与验证证据（pilot11 · 周复盘窗口口径，D1）

> 变更：pilot11-review-window（PILOT-11，T0/D1）｜实现 commit **`bc2f28c`**｜基线 `origin/main ce7be40`
> 执行人：Lead（本机）｜执行时间：2026-10-31 01:1x（Asia/Shanghai，精确保留见 pilot-log 备注）
> 环境：worktree `G:\codex_project\topicAI\pilot11-review-window`；Node v26.8.1 / pnpm 11.5.0；前端依赖 `pnpm install --frozen-lockfile` 完成

## 1. 变更范围

`git show --stat bc2f28c`：**3 files changed, 82 insertions(+), 17 deletions(-)**

| 文件 | 变化 |
|---|---|
| `frontend/src/pages/Review/ReviewPage.tsx` | 7 天/60 天双窗口取数；`compared` 取 7 天响应、`pending` 取 60 天响应；副标题窗口标注；左栏空态文案 |
| `frontend/src/pages/Review/__tests__/ReviewPage.test.tsx` | 3 → 7 个用例（窗口切分/边界/请求参数/失败/文案/空态） |
| `docs/reviews/feature-inventory.md` | J9 与 A9 歧义条目改为已决 + 新行号 |

无接口/依赖/schema/迁移变化；未改后端。

## 2. 命令与结果（原样）

### 2.1 目标测试

```
pnpm exec vitest run src/pages/Review/__tests__/ReviewPage.test.tsx --reporter=verbose
→ Test Files  1 passed (1)
  Tests       7 passed (7)
```

7 个用例：① 7 天响应渲染本周对照 + 两窗口各请求一次；② 8 天前已对照行不出现；③ 欠对账用 60 天响应，第 8/60 天 pending 都渲染（≤3 条）；④ 副标题两窗口计数；⑤ 任一请求失败显示错误且不渲染半套；⑥ 全空态文案；⑦ 展开行与项目链接。

### 2.2 构建（含 tsc -b）

```
pnpm build
→ tsc -b + vite build 通过；built in 38.10s
→ dist/assets/index-BCY23Xv4.js 245.46 kB（与 pilot10 基线一致，无体积回归）
```

### 2.3 Lint

```
pnpm lint   → exit 0（eslint . 无输出）
```

### 2.4 全量回归

```
pnpm test   （vitest run --coverage）
→ Test Files  59 passed (59)
  Tests       471 passed (471)   （基线 pilot10：59 files / 467 tests；+4 用例）
→ Coverage: All files 82.8% stmts / 74.4% branch / 77.27% funcs / 84.58% lines
→ ReviewPage.tsx 80 / 63.88 / 89.47 / 81.57
```

## 3. A1–A6 验收映射

| # | 标准 | 证据 |
|---|---|---|
| A1 | 本周对照只来自 7 天响应且 `stage !== needs_snapshot` | 用例②（8 天前 B 不出现） |
| A2 | 欠对账来自 60 天响应且 pending，不做 7 天二次过滤；第 8/60 天边界（≤3 条） | 用例③ |
| A3 | 请求恰为 `listWeekly(7)` + `listWeekly(60)` 各一次；任一失败不渲染半套 | 用例①（调用断言）+ 用例⑤ |
| A4 | 副标题与左栏空态逐字文案 | 用例④、⑥ |
| A5 | tsc/eslint/build 0；目标 + 全量回归绿 | §2.1–§2.4 |
| A6 | 仅 3 个文件；无接口/依赖/schema 变化 | §1 |

## 4. 限制与未做（如实）

- **未跑 E2E/浏览器截图**：本地未启动后端 + Playwright 登录夹具；A0 A5 已写明截图非阻塞。RG2 前如需截图，由用户/后续会话补（A9-20261031-01 复审项）。
- **未跑后端测试**：本次无后端改动（`git diff ce7be40..bc2f28c -- backend` 为空）。
- 覆盖率来自全量套件；ReviewPage 覆盖率 80/63.88/89.47/81.57（新增分支已被用例覆盖）。
- 执行时间未精确到秒，pilot-log 该行 `time_quality=unknown`，不补造时间（记录日期 2026-10-31）。
- RG0 r2/r3 的 2 minor + 2 nit 为非阻塞随修项（决策简报措辞、确认原文入库副本、节内版本标注、A9-01 归因），RG2 一并复核；未改 RG0 已批准的工件（approve 绑 `0caffb6`，实现前未改工件）。
