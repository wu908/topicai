# A5 测试证据 · pilot7 AI 断网文案（2026-10-30）

> 工件：A5｜对应 A1 验收 1–4｜代码 commit **`ad9660b`**｜档位 D0
> 环境：worktree `pilot7-ai-offline-copy`（基线 `358a8c7`）；Node v26.8.1 / pnpm 11.5.0 / vitest 4.1.10。

## 一、改动（2 源文件 + 2 测试）

| 文件 | 改动 |
|---|---|
| `frontend/src/features/companion/CompanionDialog.tsx` | AI 对话错误：`extractErrorMessage` → `extractModelErrorMessage` |
| `frontend/src/features/content/FieldSuggestions.tsx` | 字段建议错误：同上 |
| 两个对应测试 | 各补一条 `TypeError('Failed to fetch')` → 中文友好文案、且不出现 `Failed to fetch` |

## 二、验证

| 项 | 命令 | 结果 |
|---|---|---|
| 目标测试 | `pnpm exec vitest run src/features/companion/__tests__/CompanionDialog.test.tsx src/features/content/__tests__/FieldSuggestions.test.tsx` | **2 files / 13 tests passed** |
| 全量测试 | `pnpm exec vitest run` | **63 files / 488 tests passed**（原 486 + 2 新用例） |
| 类型 | `pnpm exec tsc -b` | exit 0 |
| lint | `pnpm exec eslint src/features/companion src/features/content` | exit 0 |
| 构建 | `pnpm exec vite build` | exit 0 |

## 三、行为证据

- 新增用例断言：断网（`Failed to fetch`）时显示「模型暂时连不上，你的输入还在，可以稍后重试。」；
- 同时断言页面**不再出现** `Failed to fetch`；
- 既有用例仍通过：非网络错误（如「AI 服务不可用」「网络断了」）原样显示，说明只改网络类映射、未覆盖其他错误。

## 四、限制

- 无 E2E（D0 轻量）；未跑覆盖率门槛（全量 vitest 无 `--coverage`；cosmetic）。
- 仅覆盖 `CompanionDialog` 与 `FieldSuggestions` 两处；其他 AI 组件（如 `ProjectStagePage` 已用 `extractModelErrorMessage`）不在本次范围。
