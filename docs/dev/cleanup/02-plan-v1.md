# A4 · 计划 / tickets / 测试计划（pilot 6）

> 工件：A4｜版本 v1 · 2026-10-30｜对应 A3｜档位 D1

## 1. Tickets

| ID | 标题 | 内容 | 验收 |
|---|---|---|---|
| C1 | 删模型旧导出 | 删 `stageOf`/`progressOf`/`stageLabels` + 测试块 | `tsc` 0 error |
| C2 | 删旧组件 | 删 4 组件 + 2 测试文件 | grep 0 命中 |
| C3 | 清注释 | CSS/模型/`ContentPage.tsx` 注释去掉旧组件引用 | grep -E 0 命中 |
| C4 | 验收 | 全量测试/覆盖率/tsc/eslint/build | 全绿 |

## 2. 测试计划

| 层 | 用例 | 命令 |
|---|---|---|
| 回归 | 既有 65 files / 512 tests 全绿（含 ContentPage/ProjectStagePage/ProjectFlowBar） | `pnpm exec vitest run --coverage` |
| 静态 | tsc/eslint/build | 见 A3 §3 |
| 证据 | grep 0 命中 | A3 §3 第 1 条 |

## 3. DoR

- 每 ticket 变更面 ≤6 文件；验收可命令化；无新依赖；无 UI 行为变化。

## 4. 停止条件

- 发现旧组件仍被生产引用 → 停止 C2，改范围；
- 全量测试出现与本次无关的既有失败 → 记录，不擅自改断言；
- `tsc` 报其他模块错误 → 确认非本次引入后再继续。
