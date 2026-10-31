# A5 · 测试与验证证据（pilot14 · 周复盘欠对账全量显示，D1）

> 变更：pilot14-review-pending（PILOT-14，T0/D1）｜实现 commit **`00c6059`**｜基线 `origin/main 2d08a1d`
> 执行人：Lead（本机）｜执行时间：2026-10-31 10:2x–10:3x（Asia/Shanghai）
> 声明：未启用 analytics、未修改后端/接口；部署尚未执行（待 RG3/OG0/A7）。

## 1. 变更范围

`git show --stat 00c6059`：**3 files changed, 17 insertions(+), 2 deletions(-)**

| 文件 | 变化 |
|---|---|
| `frontend/src/pages/Review/ReviewPage.tsx` | `pending.slice(0, 3)` → `pending`，渲染全部待回填 |
| `frontend/src/pages/Review/__tests__/ReviewPage.test.tsx` | +1 用例：5 条 pending 全部渲染（原 7 用例保留） |
| `frontend/e2e/async-loop.spec.ts` | 旧文案正则 `本周期` → `本周`（B-10） |

无后端/接口/schema/依赖变化。

## 2. 命令与结果（原样）

### 2.1 目标测试

```
pnpm exec vitest run src/pages/Review/__tests__/ReviewPage.test.tsx --reporter=verbose
→ Test Files  1 passed (1)
  Tests       8 passed (8)
```

含原 7 用例 + 新增「renders all pending rows (no 3-item cap)」；原「expands the row…」用例保留。

### 2.2 构建 / Lint

```
pnpm build   → tsc -b + vite build 通过（built in 50.34s）
pnpm lint    → exit 0（eslint . 无输出）
```

### 2.3 全量回归

```
pnpm test（vitest run --coverage）
→ Test Files  59 passed (59)
  Tests       472 passed (472)   （C1 基线 471；+1 用例）
→ ReviewPage.tsx coverage 80 / 63.88 / 89.47 / 81.57（与 C1 一致；新增用例覆盖渲染全量）
```

### 2.4 E2E 文案

- `frontend/e2e/async-loop.spec.ts:61` 从 `/本周期还没有可对照的判断|本周对照|欠对账/` 改为 `/本周还没有可对照的判断|本周对照|欠对账/`；
- **本地未跑 Playwright**（无后端/登录夹具）；PR CI 的 Playwright 回归作为证据。

## 3. A1–A7 验收映射

| # | 标准 | 证据 |
|---|---|---|
| A1 | 4+ 条 pending 全部渲染 | 新用例（5 条全渲染） |
| A2 | 0/≤3 条行为不变 | 原 3 条 pending 用例仍绿 |
| A3 | 失败不渲染半套 | 原失败用例仍绿 |
| A4 | E2E 正则不依赖 `本周期` | §2.4 |
| A5 | tsc/eslint/build/vitest | §2.1–2.3 |
| A6 | diff 仅 3 文件 | §1 |
| A7 | 部署时 RG3/OG0/A7 + 演练 | 待执行（下一步） |

## 4. 限制与遗留（如实）

- **未跑 E2E 本地**（依赖后端/登录）；CI 将跑 Playwright。
- RG0 r1 的 7 minor/2 nit 未改 A0（避免 RG0 approve 失效）：m1（RG1 #5 排除句）、m2（>60 pending 误引 A9-02）、m3（T0 依据）、m4（可读性接受依据）、m5（A4 正则证据）、m6（设计门 file:line）、m7（release_trigger 记录）、m8（未知项 owner/截止）；交 RG2 判断/随修。
- 部署/回滚演练**尚未执行**；RG0 明确“不授权部署”，须 RG3+OG0+A7。
- `release_trigger=deploy` 将写入 pilot-log/A7。
- 执行时间未精确到秒：A5 行 `time_quality=unknown`。
