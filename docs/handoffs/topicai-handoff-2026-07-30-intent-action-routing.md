# TopicAI Handoff — 2026-07-30

工作区：`G:\codex_project\topicAI`
主仓库（git root）：`G:\codex_project\topicAI\mvp` ← 注意不是 `topicAI`
当前分支：`main`（`HEAD: 580dd82`，与 `origin/main` 同步）
工作区状态：干净（仅 `docs/handoffs/` 下若干未跟踪的历史交接文档）

---

## 1. 现在做什么

**没有进行中的任务。** 上一轮的两条修复已合入 `main` 并在合并后的 `main` 上验证通过，无阻塞、无待提交改动。

下一个任务尚未开始，候选见第 4 节。

---

## 2. 已经完成了什么

本次会话只做一件事：修掉 `_derive_action` 把历史内容推进发布流水线的问题（承接上一轮 PR #20 里标注为「建议单独处理」的上游问题）。

两个 PR 已按顺序合入，均为 merge commit（沿用仓库既有历史风格）：

| PR | 分支 | 内容 | 合入时间 |
|---|---|---|---|
| [#20](https://github.com/wu908/topicai/pull/20) | `fix/legacy-intent-display` | 历史内容不再显示被兜底出来的发布意图 | 19:08Z |
| [#21](https://github.com/wu908/topicai/pull/21) | `fix/retrospective-action-routing` | 历史内容不再被送进发布流水线 | 19:11Z |

改动细节不在此复述 —— 看 PR #21 正文（含设计理由与取舍）和提交 `1b69d68`。一句话概括：新增终态动作 `scope_learning`，并修掉两处「替用户认领意图」的问题（`content_intent` 在 SQLite 默认 `'solve'`，orchestrator 读未归一化的行）。

相关规格与决策：`specs/010-*`（`legacy_unclassified` 的定义在第 198 行）、`docs/adr/` 下的 ADR 0002。

### 合并后在 `main` 上的验证结果

两个 PR 都改到 `backend/app/services/intent_orchestrator.py`，textual 合干净不代表语义一致，所以重跑过：

- 后端 `tests/api/v2` + `tests/integration` + `tests/data`：**124 passed, 1 deselected**（174s）
- 前端 `tsc -b` / `eslint .`：干净；`vitest run`：**380 passed / 2 skipped**（56 files）

无回归。

---

## 3. 卡在哪里

**没有卡点。**

唯一需要知道的既有噪音：`test_scenario_g_coverage_gate`（`tests/integration/test_acceptance_scenarios.py:414`）在本地全量跑会失败，这是元测试自嵌套的历史问题，CI 本来就用 `-k` 排除。**不要去「修」它。**

---

## 4. 下一步做什么

没有指定任务，以下三项按优先级排列，都需要先跟用户确认再动：

1. **观察窗口到期提醒**（此前明确推迟，不要未经指示就开工）。
2. **两条既有 LOW 发现**（都不是本次改动引入的）：
   - `backend/app/services/content_opportunity.py:315` — materials 与 intent-override 的顺序问题
   - `backend/app/services/content_genome.py:407` — `_applicability` 收到的是标量 scope key，导致混合系列看起来比全体一致的系列更适用
3. **清理远端分支** —— 仓库没开 auto-delete，`fix/legacy-intent-display` 和 `fix/retrospective-action-routing` 合入后仍留在远端。删除属于不可逆操作，需用户明确同意。

---

## 5. 哪些坑不要踩

**环境与工具链**

- git root 是 `mvp/`，不是 `topicAI/`。在 `topicAI/` 下跑 git 会报 "not a git repository"。
- 后端测试必须用 `backend/.venv/Scripts/pytest.exe`；系统 `python -m pytest` 没装 pytest。
- 迭代时加 `--no-cov` 并指定具体文件。带覆盖率的全量套件约 15 分钟（实测 949s）。
- 前端 `tsc --noEmit` **什么都不检查** —— 根 `tsconfig.json` 是 solution-style（`"files": []`）。真正的门是 `tsc -b`（`pnpm build` 跑的就是它）。
- mypy 必须带 CI 的 `--no-site-packages`，否则会报 numpy 存根里的 Python 3.12 语法错误。
- `gh` 读不了 git-bash 的 `/tmp` 路径。PR body 写到 `C:\Users\24100\AppData\Local\Temp\`。
- CI 只在指向 `main` 的 PR 上跑；堆叠 PR 拿不到任何检查，且 ruff 会在 pytest 之前就让 backend job 挂掉。

**改动约束**

- 数据库：`next_best_actions.action_type` **有 CHECK 约束**（曾误判为没有）。SQLite 不能原地改 CHECK，加动作类型需要整表重建 —— 用 `_expand_intent_action_types`（`runner.py`），别再各写一份。
- 迁移有**两条分叉路径**：文件库走 sync runner 的 `MIGRATION_POST_STEPS`；内存库（所有测试）逐个重放 `.sql` 且**跳过 post-steps**，靠 `app/core/database.py` 里手工内联重放。**加迁移要两边都改**，否则迁移测试全绿但 API 测试照样挂。
- 新迁移必须更新 `tests/data/test_content_project_calibration_migrations.py` 里**四份**穷举版本列表。
- 前端 `HomePage.tsx` 有两个 `Record<IntentAction['action_type'], string>` 穷举表，加动作类型必须补齐，否则 `tsc -b` 挂。`actionLabels` 用在主按钮上，文案要像可点击的动作而不是陈述句。
- capability 列表在 `creator_state.py` 和 `MePage.tsx` 各有一份，改要改两处。
- `_AUTO_PREPARE_CAPABILITIES` 只含 `review_candidate` / `confirm_learning`。往里加之前先确认目标不是受保护决策。受保护决策（永不自动准备、不计入 `capability_trust`）：`confirm_intent`、`lock_intent`、`create_project`、`answer_key_question`、`record_publication`、`add_performance`、`manage_learning`、`confirm_publish_scope`。
- 绝对不要重新引入全局 `candidate_acceptance_rate` 或项目数作为资格条件（ADR 0002 明令禁止，仅可展示）。
- 不要删 `backend/data/` 下的本地数据库。
- 不要直接推 `main`；一律 feature 分支 + PR。`origin` 保持 `https://github.com/wu908/topicai.git`。
- 破坏性 git 操作（force push、`reset --hard`、`clean -f`、`branch -D`）需用户明确许可。

**排查经验**

- 测试里断言 `response.json()` 之前先断言 `status_code == 200, response.text`。否则服务端 500 会伪装成 `JSONDecodeError: Expecting value: line 1 column 1`。
- 组合 SQL 字符串变换时注意 `"CREATE TABLE next_best_actions"` 是重命名后表名的**前缀**，会被改两次。`_scope_learning_table_sql` 的重命名做成幂等就是为此。
- 用 Grep 工具而不是 shell `grep -rln` 全仓搜索；后者在本仓库会超时。
- shell 的 cwd 在多次调用间是持久的。`cd` 到别处之后记得给命令加上完整前缀。

---

## Suggested skills

下一次开工按顺序用：

- `search-first` —— 动手之前先读回相关 spec 段落与既有代码（`CLAUDE.md` §2.3 要求）。
- `tdd-workflow` —— 宪法 Principle II 是硬性要求：测试必须先失败。
- `verification-loop` —— 对照 `quickstart.md` 里的验收场景。
- `code-review` —— 一个逻辑组／user story 阶段完成后跑。
- `quality-gate` —— 宣布阶段完成之前跑。
- `database-migrations` —— 只要新建 `NNN_*.sql` 就用，并配合上面关于两条迁移路径的告警。
