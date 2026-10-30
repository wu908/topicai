# A5 测试证据 · pilot10 死 CSS 清理（2026-10-30）

> 工件：A5｜对应 A1 验收 A1–A4｜代码 commit **`4c18470`**｜档位 D0
> 环境：worktree `pilot10-dead-css`（基线 `8e4d481`）；Node v26.8.1 / pnpm 11.5.0 / vitest 4.1.10。

## 一、改动

- `frontend/src/pages/Content/ContentPage.css`：删除 **40 组 / 314 行**只服务已删组件的规则（前缀 `.viewpoint-*`、`.series-*`、`.genome-context*`、`.workspace-eyebrow`，含媒体查询内规则）；**diff 全部为删除，无重排/无新增**。

## 二、验证

| 项 | 命令（cwd） | 结果 |
|---|---|---|
| 死前缀 0 命中 | `git grep -n "viewpoint-\|series-\|genome-context\|workspace-eyebrow" -- frontend/src` | CSS 0 命中（仅 API 路由字符串 `viewpoint-candidates`/`creator-series-candidates`，非样式） |
| 全量测试 | `pnpm exec vitest run`（frontend/） | **59 files / 467 tests passed**（与清理前一致） |
| 类型 | `pnpm exec tsc -b` | exit 0 |
| lint | `pnpm exec eslint src/pages/Content` | exit 0 |
| 构建 | `pnpm exec vite build` | exit 0（bundle 245.46 kB 与清理前一致） |
| diff 形态 | `git show --stat 4c18470` | 1 file, **314 deletions(–), 0 insertions** |

## 三、界面无变化论证

- 删除规则对应的类无任何元素使用（grep 仅 CSS 命中）；
- 无混合选择器（逐条前缀规则整组删除）；
- build 成功 + 全量测试绿；E2E 未本地跑（PR CI 会跑）。

## 四、限制

- E2E/视觉未本地跑；PR CI `ci-frontend`（含 E2E）将作为补充证据。
