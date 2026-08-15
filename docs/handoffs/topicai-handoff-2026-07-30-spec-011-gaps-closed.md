# TopicAI Handoff — 2026-07-30（Spec-011 缺口关闭）

工作区：`G:\codex_project\topicAI`  
主仓库（git root）：`G:\codex_project\topicAI\mvp`  
当前分支：`main`（`HEAD: 947336e`，与 `origin/main` 同步）  
远端分支：仅 `origin/main`  
工作区状态：无待提交代码改动；`docs/handoffs/` 下有未跟踪交接文档，含本文。

> 承接 `docs/handoffs/topicai-handoff-2026-07-30-opportunity-materials-fixed.md`。本轮实现、审查与 CI 详情以 [PR #24](https://github.com/wu908/topicai/pull/24) 为准，本文不重复完整 diff。

---

## 1. 现在做什么

**没有进行中的代码任务。** 用户要求的三个缺口修复、重新审查、提交、创建 PR、合并及远端分支清理均已完成。

当前只是在保存本交接文档。下一项开发任务尚未指定；不要未经确认自行开工。

---

## 2. 已经完成了什么

本轮关闭了 Spec-011 复审确认的三个缺口：

1. 延展机会 UI 显示并允许修改 AI 提议的内容意图与格式，确认后的值会下传 API。
2. 混合系列确认后，Creator State insight 保存权威 `member_intents`。
3. 混合意图或格式时，`scope` 省略对应标量键，不再写 `null`。

复审期间还修复了 Migration 037 的恢复问题：列已创建但迁移版本尚未记录时可以安全重放。

- feature commit：`68f53c8`（`fix: close creator series review gaps`）
- PR：[GitHub #24](https://github.com/wu908/topicai/pull/24)
- merge commit：`947336ecd1d62644285159816daa86c02baea917`
- Standards 复审：无发现
- Spec 复审：无发现
- 后端：379 passed，1 deselected
- 前端：380 passed，2 skipped
- `ruff`、`mypy`、ESLint、TypeScript、production build：全部通过
- PR CI：`ci-backend`、`ci-frontend` 均成功

远端清理也已完成：PR 分支以及已合入的 `feature/creator-series-scope` 均已删除；`git ls-remote --heads origin` 只返回 `main`。本地 `main` 已 fast-forward 到上述 merge commit。

此前完成的机会素材修复见 `docs/handoffs/topicai-handoff-2026-07-30-opportunity-materials-fixed.md` 和 [PR #23](https://github.com/wu908/topicai/pull/23)。

---

## 3. 卡在哪里

**没有卡点。**

两个已知环境噪音不属于待修问题：

- `test_scenario_g_coverage_gate` 本地全量运行会因覆盖率元测试自嵌套失败；现有回归约定排除它。
- Git HTTPS 在本机偶发 DNS 或连接重置；原样重试通常恢复，不要改 Git/SSL 配置。

---

## 4. 下一步做什么

唯一剩余候选是 **观察窗口（Observation Window）到期提醒**：

- `publish_hypotheses.observation_window_days` 已入库。
- 调度任务与通知逻辑尚未实现。
- 该项此前被明确推迟，必须先由用户确认范围后再开工。

需求来源与原始候选说明见 `docs/handoffs/topicai-handoff-2026-07-28-spec-010-complete.md` 第 4 节。若用户确认，按仓库流程从 `main` 新建 feature 分支，先完成 Research / Plan，再用 TDD 实现，最后做 Standards 与 Spec 双轴审查并通过 PR 合入。

---

## 5. 哪些坑不要踩

- git root 是 `mvp/`，不是外层 `topicAI/`。
- 仓库存在 `.codegraph/`；理解或定位代码时先用 CodeGraph，再按需使用 `rg`。
- 不要直接推送 `main`；继续使用 feature 分支与 PR。
- 远端现在仅有 `main`，不要重复执行分支清理。
- 不要提交、删除或改写其他未跟踪交接文档，除非用户明确要求。
- Spec-011 中成员集合是混合系列的权威事实；成员不一致时省略 `scope.content_intent` / `scope.format`, 不要用 `null` 代替省略。
- 延展机会必须把用户最终确认的意图与格式传给 API，不能只展示 AI 建议后仍提交旧值。
- Migration 037 必须兼容“schema 已变更、版本记录未写入”的恢复场景，不能把重放重新变成阻断。
- 后端测试使用 `backend/.venv/Scripts/pytest.exe`；mypy 带 `--no-site-packages`；本地回归继续排除 `test_scenario_g_coverage_gate`。
- Git HTTPS 抽风时原样重试；不要改 SSL backend、HTTP version，也不要手工造 merge commit。
- 不要删除 `backend/data/` 下的本地数据库。

---

## Suggested skills

下一次开工建议按任务选择：

- `codebase-design`：确认观察窗口调度、通知与现有领域边界应放在哪里。
- `tdd`：行为变更先写最小失败测试，再实现。
- `code-review`：完成后按 Standards / Spec 两个轴复审。
- `github:github`：创建 PR、核对 CI 与合并状态。
- `ponytail:ponytail`：复用已有调度与通知路径，避免为单一需求新增框架。
- `diagnose`：仅在出现难复现缺陷时进入根因诊断循环。

> 本交接文档由 AI 辅助整理，已依据本地 git 状态、PR #24、CI 结果及现有交接文档核对。
