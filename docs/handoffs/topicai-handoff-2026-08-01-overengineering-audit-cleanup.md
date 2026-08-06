# TopicAI Handoff - 2026-08-01 (Over-engineering Audit Cleanup)

> 本文档由 AI 辅助整理，依据本地 Git 差异、测试、Docker 构建和运行结果校对；未记录密钥、令牌或本地敏感配置。

工作区：`G:\codex_project\topicAI\mvp`

分支：`feature/explainable-opportunities`

当前 HEAD：`28151b7` - `refactor: remove verified over-engineering`

## 当前状态

全仓库过度工程复审、确认删除、验证和提交已经完成。范围仅限本仓库；不要操作 `G:\codex_project\no.2_project\product_drill_AI`。

清理提交为 `28151b7`，父提交为 `08f289c`。完整差异以 `git diff 08f289c..28151b7` 为准，统计为：`88 files changed, 306 insertions, 8577 deletions`。提交前 `git diff --cached --check` 已通过。

除本交接文档的状态更新外，本次清理没有未提交代码差异。工作树仍包含用户已有的 `AGENTS.md` 修改和其他未跟踪项目文档。

## 已完成工作

本次按 `ponytail-audit` 的删除优先原则处理已验证的过度工程，主要包括：

- 删除未被生产代码调用的前端组件、API wrapper 及其自验证测试。
- 删除 Tailwind/PostCSS 配置链和 4 个直接前端开发依赖；保留根目录 `pnpm-lock.yaml`，删除前端重复 lockfile。
- 删除后端重复配置、未使用内容分析器、Chroma/本地存储包装、测试专用模型和错误处理器。
- 删除无生产调用方的 PromptRegistry 与 prompt 文件；效果复盘链直接复用已有内联 prompt 常量。
- 删除未实现的备份、健康检查和内容清理任务，仅保留真实使用的观察窗口提醒调度。
- 删除重复 migration 调用、递归 pytest 覆盖率测试、空构造函数、失效设置和 Compose 旧字段/旧卷声明。
- 精简 monitoring/observability 兼容入口，但保留现有调用方需要的兼容表面。
- 同步 `requirements.txt`、`pyproject.toml`、`package.json` 和两个保留的 lockfile。

刻意保留的内容：v1 兼容接口、旧前端回滚页面、根目录 pnpm lockfile、`zhipuai`、monitoring/observability 兼容入口。不要在没有生产调用证据或迁移计划时继续删除这些内容。

处理中曾发现 6 个 Python 文件被批量编码操作破坏。已从 HEAD 恢复原始 UTF-8 内容并仅重做必要删除；随后通过 Python 编译、Ruff 和相关测试。当前没有已知乱码回归。

## 验证结果

- Ruff：通过。
- 后端删除边界定向测试：`104 passed`。
- 前端 ESLint：通过。
- 前端生产构建：通过。
- 前端 Vitest：`50 passed` test files；`366 passed, 1 skipped` tests。
- 后端全量：`812 passed, 1 failed`。
- 后端覆盖率：`87.78%`，通过 80% 门禁。
- Docker Compose：`up --build -d --wait` 通过，backend/frontend 均 Healthy。
- HTTP 冒烟：后端 `/api/v1/health` 返回 200；前端 `/` 返回 200。
- 验证后已执行 `docker compose down`，未使用 `-v`，并已关闭 WSL。

唯一失败为既有基线问题：

`backend/tests/api/v2/test_experiment_metrics.py::test_action_funnel_has_stable_denominator_and_safe_events`

断言预期 `funnel["offered"] == 1`，实际为 `0`。该失败在本次删除前已存在，当前差异未触及对应业务实现；如需处理，必须先确认指标事件和稳定分母契约，不能直接改断言掩盖行为。

容器构建期间 npm 报告 2 个 moderate vulnerability；本轮未执行可能带来破坏性升级的 `npm audit fix --force`。Vite 还提示 `vite.config.ts` 的 `__dirname` 未来不兼容 native config loader，当前构建不受影响。

## Docker 卷状态

已按用户确认删除 8 个空旧卷。当前剩余：

- `mvp_topicai_data`：当前项目数据库卷，保留。
- `mvp_topicai_logs`：当前 Compose 日志卷，保留。
- `topicai-fix-review_topicai_data`：历史验证数据，约 1.065 MB；删除前需用户确认。
- `topicai-fix-smoke_topicai_data`：历史验证数据，约 1.065 MB；删除前需用户确认。

## 工作树边界

用户已有的 [`AGENTS.md`](../../AGENTS.md) 修改，以及 `docs/agents/`、`docs/handoffs/` 下其他未跟踪文档，不属于本次代码清理。不得覆盖、删除、批量暂存或默认提交。本交接文档已包含在 `28151b7` 中；当前这次状态更新尚未提交。

开发和容器命令继续遵守 [`AGENTS.md`](../../AGENTS.md) 的 WSL-first 规则。WSL 会报告 systemd 用户会话警告；Docker 命令仍可运行。Windows PowerShell 执行策略会拦截 `npm.ps1` 和部分全局脚本，必要时使用 `npm.cmd`，不要修改系统执行策略。

## 建议后续顺序

1. 使用 `git show 28151b7` 审阅已提交的删除范围和保留决策，不再扩展清理范围。
2. 如需提交本次交接状态更新，只暂存本文件，排除 `AGENTS.md` 和其他用户文档。
3. 是否修复 experiment metrics 失败由用户决定；先诊断指标契约，再做最小根因修复。
4. 若后续代码继续变化，在提交或 PR 前重新运行相关测试、全量门禁和 Compose 健康检查。
5. 两个历史 data 卷只有在用户明确确认不需要回滚数据时才删除。

## Suggested skills

- `code-review`：审查提交 `28151b7`，重点检查行为回归、错误删除和测试缺口。
- `diagnose`：定位 experiment metrics 中 `offered` 计数为 0 的根因并核对指标契约。
- `ponytail-review`：仅在继续清理时使用，要求每项删除都有生产调用证据；不要重新发起无边界全仓库重构。
- `handoff`：下一阶段完成后更新状态，引用本文件、提交和测试结果，不复制完整 diff。
