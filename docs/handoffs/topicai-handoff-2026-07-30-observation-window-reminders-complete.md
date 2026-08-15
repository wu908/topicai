# TopicAI Handoff — 2026-07-30（Observation Window 提醒完成）

工作区：`G:\codex_project\topicAI`  
Git 根目录：`G:\codex_project\topicAI\mvp`  
当前分支：`main`  
当前提交：`4ee5c7c76eed53b6b0692a8233c9c34a0186c7f2`，与 `origin/main` 同步  
完成 PR：[GitHub #25 — Add observation window reminders](https://github.com/wu908/topicai/pull/25)

---

## 1. 现在做什么

**没有进行中的代码任务。** Observation Window 到期提醒已经实现、复审、通过 CI 并合入 `main`，远端只剩 `main`。

下一次会话建议先确认是否开始“**结果明确不可用时也能完成复盘闭环**”。这是当前最直接的用户闭环缺口，但尚未获得开工确认，不要自行实现。

项目目录下仍有多份未跟踪的交接文档，包括本文；除非用户明确要求，不要批量提交、删除或改写它们。

---

## 2. 已经完成了什么

Observation Window 提醒闭环已完成：

- 新增 `ObservationWindowService.mark_due(as_of)`，按真实发布时间和 `observation_window_days` 将到期项目从 `published` 推进到 `awaiting_review`。
- 复用现有 APScheduler：应用启动时立即检查，此后每 15 分钟检查一次。
- 到期前，Today 与项目工作区显示 `await_observation_window` 和准确结束时间；到期后显示回填实际表现动作。
- 保留用户主动提前开始复盘的既有能力；Observation Window 是主要复盘时间，不是强制禁录期。
- 新增 Migration 039，使 `next_best_actions.action_type` 接受 `await_observation_window`，兼容文件数据库、内存数据库和迁移恢复。
- 没有新增通知中心、推送系统或通知表；项目状态和 Today 下一动作就是持久站内提醒。

实现细节、提交和最终 diff 以 [PR #25](https://github.com/wu908/topicai/pull/25) 为准：

- 功能提交：`0f47b6c feat: add observation window reminders`
- 复审修复：`ce2d5fd fix: preserve user-started observation review`
- 合并提交：`4ee5c7c Merge pull request #25 from wu908/feature/observation-window-reminders`

验证结果：

- 后端受影响测试：`80 passed`
- 前端：`381 passed, 2 skipped`
- Ruff、mypy（144 个源文件）、ESLint、TypeScript、production build、`git diff --check`：全部通过
- GitHub Actions：[run 30546992301](https://github.com/wu908/topicai/actions/runs/30546992301) 成功，`ci-backend` 与 `ci-frontend` 均通过

Standards / Spec 双轴复审中发现的唯一功能回归是“到期前禁止用户主动回填”，已经修复。其余意见属于仓库既有的跨领域基础设施缺口或既有迁移惯例，没有扩进本次提醒 PR。

---

## 3. 卡在哪里

**当前没有阻塞。** Git、PR、CI 和本地验证均已收口。

下一项候选尚缺用户对范围的明确确认。已知但未在 PR #25 中扩建的事项：

- `CONTEXT.md` 要求“结果明确不可用”仍能产生 unknown Intent Outcome 并关闭 Reviewed Content Loop；当前快照入口至少要求一个平台指标。
- 仓库尚无完整的追加式 `ProjectStateEvent` 基础设施；现有状态转换普遍使用 `last_action` / `last_action_at`。
- 部分 `/api/v2` 路由仍返回未参数化 `ApiResponse`，完整响应模型属于跨模块治理工作。
- Spec-009 提到的 Today 全场景优先级矩阵尚未形成独立完整测试集。

这些事项不要在没有独立范围和测试 seam 的情况下顺手混入一个补丁。

---

## 4. 下一步做什么

推荐优先处理“**无可用指标也能完成复盘闭环**”，因为它直接影响发布后的用户主流程。

开工前先完成 Research / Plan，并与用户确认最小行为边界：

1. 明确“结果不可用”与“指标为 0”是不同事实，不能用全零快照代替 unavailable。
2. 明确用户如何声明暂时或最终拿不到数据，以及是否必须填写原因/来源状态。
3. 明确 unavailable 结果如何进入 Blind Review / Intent Outcome，并确保最终结论只能是 `unknown`，仍可选择下一步。
4. 确认 TDD seams，建议至少覆盖：后端结果提交边界、`/api/v2/today` / 项目工作区入口、unknown 闭环状态。
5. 从最新 `main` 新建 feature 分支，按 TDD 实现，完成 Standards / Spec 双轴复审后通过 PR 合入。

后续优先级建议：

1. 无指标结果闭环。
2. 项目状态追加式审计。
3. `/api/v2` 完整 Pydantic 响应模型。
4. Today 多任务优先级矩阵测试。

---

## 5. 哪些坑不要踩

- Git 根目录是 `G:\codex_project\topicAI\mvp`，不是外层 `topicAI`。
- 仓库存在 `.codegraph/`；理解或定位代码时先用 CodeGraph。PowerShell 下可调用 `G:\nodejs\node_global\codegraph.cmd`。
- 不要直接推送 `main`；开发走 feature 分支和 PR。
- 不要把 Observation Window 重新做成强制禁录期；已有数据时用户必须仍可主动开始复盘。
- 不要把 unavailable 伪装为数值 `0`，也不要让 unknown 结果暗示成功、失败或因果关系。
- 不要为单一需求新增通知中心、消息总线或第二套工作流；优先复用现有 Content Project、Today 和 Next Best Action。
- 不要顺手补齐所有状态审计或所有 v2 响应模型；它们需要独立范围，否则会把小功能变成跨仓库重构。
- Migration 039 使用编号 SQL 文件登记并由 runner 的幂等 post-step 重建 SQLite CHECK；修改时必须保留文件数据库、内存数据库和中断恢复兼容性。
- 后端测试使用 `backend/.venv/Scripts/pytest.exe`；全量约定继续排除 `test_scenario_g_coverage_gate`。
- mypy 在 `backend/` 下运行：`.\.venv\Scripts\mypy.exe --no-site-packages app`。
- PowerShell 执行策略可能拦截 `pnpm.ps1`；使用 `G:\nodejs\node_global\pnpm.cmd`。
- Git HTTPS 偶发 DNS/连接重置时原样重试，不要修改 Git/SSL 配置。
- 不要删除 `backend/data/` 下的本地数据库。
- 不要提交、删除或覆盖 `docs/handoffs/` 下其他未跟踪文档，除非用户明确要求。

---

## Suggested skills

- `domain-modeling`：先明确 unavailable result、unknown Intent Outcome 和 Reviewed Content Loop 的领域边界。
- `codebase-design`：定位结果状态应复用的现有模型、服务与动作协议，避免新增平行工作流。
- `tdd`：与用户确认公共 seams 后，按红灯 → 最小实现 → 绿灯推进。
- `code-review`：完成后按 Standards / Spec 两个轴复审最终 diff。
- `github:github`：推送 feature 分支、创建 PR、核对 CI、合并和清理远端分支。
- `ponytail:ponytail`：优先复用现有状态和动作路径，不为单一 unavailable 状态扩建框架。
- `diagnose`：仅在出现难复现的状态推进、迁移或并发问题时使用。

> 本交接文档由 AI 辅助整理，已依据本地 Git 状态、PR #25、GitHub Actions 结果、现有规范与本轮复审记录核对。
