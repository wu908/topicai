# TopicAI Handoff - 2026-07-31 (Project State Event 已合并)

> 本文档由 AI 辅助整理，并依据本地 Git 状态、PR #27、GitHub CI 和本轮验证结果校对。

工作区：`G:\codex_project\topicAI`
Git 根目录：`G:\codex_project\topicAI\mvp`
当前本地分支：`feature/project-state-event-plan`
功能提交：`c7d67b8` - `feat: add audited project state transitions`
已合并 PR：[GitHub #27](https://github.com/wu908/topicai/pull/27)
`origin/main`：`17113fa` - `Merge pull request #27 from wu908/feature/project-state-event-plan`

## 当前状态

Project State Event 已实现、验证并合入 `main`，没有待提交的跟踪代码改动。

本地 `main` 仍停在 PR #26 的合并提交 `173a1ee`；`origin/main` 已通过临时 SSH fetch 刷新到 `17113fa`。如下一会话需要在本地 `main` 开工，先执行：

```powershell
git switch main
git merge --ff-only origin/main
```

工作区中仍有多份未跟踪的 `docs/handoffs/` 文档。它们是用户资产，不要批量提交、删除或覆盖。`backend/data/` 下的本地数据同样不得删除。

## 本轮交付

实现范围和设计决策以以下已有产物为准，不在本文重复展开：

- [`CONTEXT.md`](../../CONTEXT.md)：Project State Event 领域定义。
- [`specs/008-content-project-mvp/project-state-event-plan.md`](../../specs/008-content-project-mvp/project-state-event-plan.md)：实施计划、边界和验收标准。
- [`backend/app/data/migrations/041_project_state_events.sql`](../../backend/app/data/migrations/041_project_state_events.sql)：追加式状态事件表与索引。
- [`backend/app/services/project_state.py`](../../backend/app/services/project_state.py)：规范状态图、所有权/版本校验、幂等回放与内部原子 `apply()`。
- [`backend/app/api/v2/projects.py`](../../backend/app/api/v2/projects.py)：`POST /api/v2/projects/{project_id}/transitions`。
- [`backend/tests/services/test_project_state.py`](../../backend/tests/services/test_project_state.py)：公共转换、幂等与工作流边界测试。
- [PR #27](https://github.com/wu908/topicai/pull/27)：最终 diff、讨论和 CI 记录。

关键边界：公共转换接口只允许 `inbox -> preparing`、`preparing -> inbox | creating`、`creating -> preparing`。发布假设锁定、发布、复盘、结算和证据回滚必须继续由所属工作流调用内部 `ProjectStateService.apply()`，不能从公共接口绕过附带事实。

最终生产代码扫描确认：只有 `ProjectStateService` 直接写入 `content_projects.status`。

## 验证结果

- 后端完整套件：`850 passed, 1 deselected`。
- 后端覆盖率：`87.39%`，门槛为 `80%`。
- Ruff：通过。
- mypy：通过，`149` 个源文件。
- Bandit：通过。
- `git diff --check`：通过。
- GitHub Actions：`ci-backend` 和 `ci-frontend` 均通过。

已知低优先级提示：pytest 仍提示 `asyncio_default_fixture_loop_scope` 未显式配置。这不是本次功能回归；需要统一测试事件循环策略时再单独处理。

## 建议下一步

默认产品优先级建议转向 **Growth onboarding / 历史内容导入 / 可纠正创作者画像**。这是上一份交接中识别的主要用户价值缺口，但业务范围尚未在本轮确认；下一会话应先让用户确认三者的优先顺序和 MVP 边界，再开始改代码。

相关背景：

- [`topicai-handoff-2026-07-30-unavailable-result-merged.md`](./topicai-handoff-2026-07-30-unavailable-result-merged.md)
- [`specs/008-content-project-mvp/tasks.md`](../../specs/008-content-project-mvp/tasks.md)
- [`specs/008-content-project-mvp/`](../../specs/008-content-project-mvp/)

如果用户选择继续架构治理，候选项是 `/api/v2` Pydantic response models 或 Today 全场景优先级矩阵；不要在未确认优先级时并行展开。

## 约束与注意事项

- 仓库存在 `.codegraph/`；理解或定位代码时先使用 CodeGraph。
- 使用 feature 分支和 PR，不直接推送 `main`。
- 不得重新引入对 `content_projects.status` 的直接写入。
- 不要把 Project State Event 扩展成全仓库事件溯源系统；当前实现是最小审计边界。
- 保持未知结果语义：unavailable 不等于数值 `0`，unknown outcome 不产生 Validated Insight。
- HTTPS 到 GitHub 在本轮曾无法连接；SSH 端口可用。若再次发生，可使用临时 SSH fetch，不必修改 `origin` URL。

## Suggested skills

- `domain-modeling`：在 Growth onboarding、历史内容与画像之间明确领域边界和术语。
- `codebase-design`：优先复用现有 onboarding、profile、account data 和 project 模块。
- `tdd`：先固定导入幂等、用户纠正和数据所有权行为。
- `code-review`：实现完成后按 Standards / Spec 双轴复审。
- `ponytail:ponytail`：维持最小范围，避免提前建设通用导入平台或画像框架。
- `diagnose`：仅在出现难复现的迁移、并发或状态恢复问题时使用。
