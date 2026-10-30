# A5 测试证据 · pilot8 ArtifactPane 断网文案（2026-10-30）

> 工件：A5｜对应 A1 验收 1–4｜代码 commit **`029211d`**｜档位 D0
> 环境：worktree `pilot8-artifactpane-offline`（基线 `4b2103f`）；Node v26.8.1 / pnpm 11.5.0 / vitest 4.1.10。

## 一、改动（2 文件）

| 文件 | 改动 |
|---|---|
| `frontend/src/features/content/ArtifactPane.tsx` | 发前检查加载/运行错误：`extractErrorMessage` → `extractModelErrorMessage`（2 处） |
| `frontend/src/features/content/__tests__/ArtifactPane.test.tsx` | 补 1 条 `TypeError('Failed to fetch')` → 中文友好文案、且不出现 `Failed to fetch` |

## 二、验证

| 项 | 命令 | 结果 |
|---|---|---|
| 目标测试 | `pnpm exec vitest run src/features/content/__tests__/ArtifactPane.test.tsx` | **17 tests passed**（原 16 + 1） |
| 全量测试 | `pnpm exec vitest run` | **63 files / 489 tests passed**（原 488 + 1） |
| 类型 | `pnpm exec tsc -b` | exit 0 |
| lint | `pnpm exec eslint src/features/content` | exit 0 |
| 构建 | `pnpm exec vite build` | exit 0 |

## 三、行为证据

- 断网时显示「模型暂时连不上，你的输入还在，可以稍后重试。」且不出现 `Failed to fetch`；
- 既有非网络错误用例仍绿（「发前检查服务不可用」「检查服务超时」原样显示）。

## 四、限制

- 无 E2E（D0 轻量）；未跑覆盖率门槛（全量无 `--coverage`）。
- 仅覆盖发前检查两处；其他组件错误处理不在本次范围。
