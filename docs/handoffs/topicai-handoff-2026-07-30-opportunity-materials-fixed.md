# TopicAI Handoff — 2026-07-30（第三轮）

工作区：`G:\codex_project\topicAI`  
主仓库（git root）：`G:\codex_project\topicAI\mvp`  
当前分支：`main`（`HEAD: 16c2977`，与 `origin/main` 同步）  
工作区状态：无待提交代码改动；`docs/handoffs/` 下的交接文档为未跟踪文件，含本文。

> 承接 `docs/handoffs/topicai-handoff-2026-07-30-low-findings-closed.md`。该文档第 4 节第 2 项已经完成并合入；其余候选仍未开工。

---

## 1. 现在做什么

**没有进行中的任务。** 本轮修复已经合入 `main`，本地也已快进到远端 merge commit；无阻塞、无待提交代码改动。

下一项任务尚未指定。第 4 节列出的候选都必须先由用户确认。

---

## 2. 已经完成了什么

完成了“接受内容机会后，`material_requirements` 没有下传到新项目”的根因修复：

- PR：[GitHub #23](https://github.com/wu908/topicai/pull/23)
- feature commit：`d3e7dd4`（`fix: preserve opportunity material requirements`）
- merge commit：`16c2977`
- 分支：`fix/opportunity-material-requirements`（远端仍保留）

实现保持在两个文件内：

- `backend/app/services/content_opportunity.py`：`_ensure_project()` 不再直接用 SQL 把项目标记成 `working_confirmed`，而是复用既有 `IntentConfirmationService.confirm()`，把机会已确认的 intent、audience change 和 material requirements 一次性写入项目，同时保留正式确认路径的审计事件与后续动作语义。
- `backend/tests/services/test_creator_series.py`：在现有 `test_intent_override_without_materials_rederives_requirements` 中补充项目级素材需求断言。

详细根因与改动说明见 PR #23，不在本文重复展开。

### 验证结果

- TDD RED：新增断言先失败，项目的 `material_requirements` 实际为 `[]`。
- TDD GREEN：目标测试通过。
- `backend/tests/services/test_creator_series.py`：17 passed。
- `backend/tests/api/v2/test_creator_series.py`：2 passed。
- `tests/api/v2 + tests/integration + tests/data + tests/services`：378 passed，1 deselected（按既有规则排除 `test_scenario_g_coverage_gate`）。
- `ruff check .`：通过。
- `mypy --no-site-packages app`：143 个文件无问题。
- PR CI：`ci-backend`、`ci-frontend` 均成功。
- 未跑前端本地测试：本轮只改后端，HTTP/前端契约没有变化；前端 CI 已通过。

---

## 3. 卡在哪里

**没有卡点。**

仍有两个已知环境噪音，不属于本项目修复范围：

- `test_scenario_g_coverage_gate` 本地全量运行会因覆盖率元测试自嵌套失败；CI 和本轮回归均按既有约定排除它。
- Git HTTPS 在本机存在间歇性 DNS/连接重置。本轮合并后的第一次、第二次 fetch 分别报 `Could not resolve host` 和 `Recv failure: Connection was reset`，第三次原样重试成功；不要为此改 Git/SSL 配置。

---

## 4. 下一步做什么

没有指定任务。候选按优先级如下，**均需先向用户确认**：

1. **观察窗口到期提醒**：此前明确推迟，未经指示不要开工。
2. **清理已合并的远端分支**：当前 `origin/main` 已包含以下分支，但删除远端分支需要用户明确授权：
   - `feature/creator-series-scope`
   - `feature/retrospective-intent-ui`
   - `fix/intent-override-materials-and-series-scope`
   - `fix/legacy-intent-display`
   - `fix/opportunity-material-requirements`
   - `fix/retrospective-action-routing`

如果用户指定其他任务，以用户的新任务为准。

---

## 5. 哪些坑不要踩

- git root 是 `mvp/`，不是外层 `topicAI/`。
- 仓库有 `.codegraph/`；理解或定位代码时先用 `codegraph_explore`。PowerShell 会拦截 `codegraph.ps1`，优先调用 MCP 工具，不要因此放弃 CodeGraph。
- 不要再次在 `_ensure_project()` 里直接写 `intent_status`。项目素材需求、确认事件和下一动作必须走 `IntentConfirmationService.confirm()` 这一条正式路径。
- 后端测试使用 `backend/.venv/Scripts/pytest.exe`；迭代时带 `--no-cov`。mypy 必须带 `--no-site-packages`。
- 本地回归集合继续排除 `test_scenario_g_coverage_gate`；不要把该历史元测试噪音当成本轮回归。
- Git HTTPS 抽风时原样重试；不要改 SSL backend、HTTP version 或手工造 merge commit。
- 不要直接推 `main`；继续使用 feature 分支和 PR。
- 不要删除 `backend/data/` 下的本地数据库。
- 不要提交、删除或改写现有未跟踪交接文档，除非用户明确要求。
- 删除远端分支属于破坏性操作，必须先取得用户明确同意。

---

## Suggested skills

下一次开工建议按任务选择：

- `tdd`：任何行为变更先写失败测试，再做最小实现。
- `code-review`：逻辑组完成后检查从 `main` 固定点开始的 diff。
- `github:github`：核对 PR、CI、合并状态或远端分支时使用。
- `diagnose`：遇到新的难复现缺陷时先走根因诊断循环。
- `ponytail:ponytail`：保持最少文件、复用现有正式路径，避免新增抽象。

> 本交接文档由 AI 辅助整理，已依据本地 git 状态、PR #23 和 CI 结果核对。
