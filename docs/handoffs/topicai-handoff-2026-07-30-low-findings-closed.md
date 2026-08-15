# TopicAI Handoff — 2026-07-30(第二轮)

工作区：`G:\codex_project\topicAI`
主仓库（git root）：`G:\codex_project\topicAI\mvp` ← 注意不是 `topicAI`
当前分支：`main`（`HEAD: 5ece615`，与 `origin/main` 同步）
工作区状态：干净（仅 `docs/handoffs/` 下若干未跟踪的历史交接文档，含本文）

> 承接 `topicai-handoff-2026-07-30-intent-action-routing.md`。那份文档第 4 节列的第 2 项已完成，其余两项仍未开工。

---

## 1. 现在做什么

**没有进行中的任务。** 本轮任务已合入 `main` 并核对完毕，无阻塞、无待提交改动。

下一个任务尚未开始，候选见第 4 节 —— 三项都需要先跟用户确认。

---

## 2. 已经完成了什么

本轮只做一件事：修掉上一份交接文档第 4 节第 2 项列的**两条既有 LOW 发现**（都不是上一轮 PR #20/#21 引入的）。

| PR | 分支 | 合入时间 | merge commit |
|---|---|---|---|
| [#22](https://github.com/wu908/topicai/pull/22) | `fix/intent-override-materials-and-series-scope` | 08:32Z | `5ece615` |

改动细节、设计取舍、根因分析全在 **PR #22 正文**里，不在此复述。一句话概括两处：

1. `content_opportunity.decide()` —— materials 的默认值原先在 `confirmed_content_intent` 解析**之前**就取好，导致「覆盖意图 + 不显式传素材」会存下自相矛盾的机会行。改为先解析覆盖意图再决定 materials。
2. `content_genome.search()` —— `_applicability` 只读标量 scope key，而标量在成员不一致时是 NULL（Spec-011 以成员集合为权威），于是混合系列被判得比一致系列更适用。新增 `_member_dimension` 把成员集合折叠成 `_match_status` 要比的单值。

**一处值得记住的认知修正**：这条发现实际咬到的是 **format** 维度，不是原交接文档措辞侧重的 intent —— `_match_status` 根本不比 `intent`，那个维度由函数前面的 `continue` 守卫处理。

**刻意保留的取舍**：对外 emit 的 `applicability` 仍按行的标量派生，只有喂给 `_match_status` 的那份换成成员集合。所以 `ContentGenomeSeriesContext` 契约不变、前端零改动；节点上的 `member_intents` / `member_formats` 已经带着权威集合供调用方自行判断。改这里之前先想清楚要不要动契约。

### 验证结果

- 两个新测试先失败后通过（宪法 Principle II）：`test_intent_override_without_materials_rederives_requirements`、`test_mixed_format_series_is_not_more_applicable_than_uniform`（均在 `tests/services/test_creator_series.py`）
- `tests/api/v2 + tests/integration + tests/data + tests/services`：**378 passed, 1 deselected**（211s）
- `ruff check`：干净；`mypy --no-site-packages app`：143 个文件无问题
- PR CI：ci-backend 与 ci-frontend 均 pass
- **合并后无需重跑**：merge commit 父提交是 `580dd82` + `3a99158`，期间无其他提交落地，`git diff 3a99158 5ece615` 为空 —— 合并后的树与跑过 378 个测试的树逐字节相同。上一轮之所以要重跑，是因为两个 PR 改了同一个文件；这次不存在那个风险。判断要不要重跑就用这个方法，别凭感觉。
- 未跑前端：本轮只动后端，且刻意保持对外契约不变。

---

## 3. 卡在哪里

**没有卡点。**

两个已知噪音，都**不要去「修」**：

- `test_scenario_g_coverage_gate`（`tests/integration/test_acceptance_scenarios.py:414`）本地全量跑会失败，元测试自嵌套的历史问题，CI 本来就用 `-k` 排除。
- 每条 Bash 调用都会打 `/c/Users/24100/.bashrc: line 1: $'\377\376export': command not found`。是 `.bashrc` 的 BOM/UTF-16 编码问题，与本项目无关，不影响任何命令。

---

## 4. 下一步做什么

没有指定任务。以下按优先级排列，**都需要先跟用户确认再动**：

1. **观察窗口到期提醒** —— 此前明确推迟，不要未经指示就开工。
2. **接受机会后 `material_requirements` 不下传到项目**（本轮分析时顺带发现，比刚修的顺序问题范围大，已写进 PR #22 正文）：`_ensure_project` 建项目时不传 `material_requirements`，还把 `intent_status` 直接设成 `working_confirmed` 绕过 `confirm_intent` —— 而 `backend/app/services/intent_actions.py:84` 是**唯一**会写项目 `material_requirements_json` 的地方。结果是接受一条机会之后项目的素材需求一直是 `'[]'`，MaterialsPage 显示「素材需求待明确」。动之前先想清楚是补下传、还是让 `_ensure_project` 走正规的 `confirm_intent` 路径。
3. **清理远端分支** —— 仓库没开 auto-delete，已合入但仍留在远端的有三个：`fix/legacy-intent-display`、`fix/retrospective-action-routing`、`fix/intent-override-materials-and-series-scope`。删除属于不可逆操作，**需用户明确同意**。

---

## 5. 哪些坑不要踩

### 本轮新增

- **git 的 https 在这台机器上间歇性抽风，不是真的断网。** 会连着报 `Could not resolve host` / `Recv failure: Connection was reset` / `Failed to connect to github.com:443 after 21s` / schannel `recv returned error 56`，连挂四五次之后不改任何配置就能成功。同一时刻 `curl https://github.com` 返回 200、`curl` 打 `…/info/refs?service=git-upload-pack` 返回 401（私有仓库的正确响应）、`gh api` 正常。代理没配，换 `http.sslBackend=openssl`、`http.version=HTTP/1.1`、放宽 `http.lowSpeedLimit`/`lowSpeedTime` **都没用**。**直接重试，别去诊断。**
- **重试循环要判 git 自己的退出码，不要判管道的。** `if git fetch origin main | tail -2; then` 永远为真（读到的是 `tail` 的状态），会假装第一次就成功。写成 `if git fetch origin main >/tmp/f.log 2>&1; then`，失败时再打日志。
- **fetch 失败时绝对不要在本地手工造 merge commit** 绕过去 —— 会和远端自己的 merge commit 分叉。让本地分支落后着，等 fetch 通了再 fast-forward。

### 沿用上一份交接文档（原文有更全的清单，这里只留必读项）

**环境与工具链**

- git root 是 `mvp/`，不是 `topicAI/`。
- 后端测试必须用 `backend/.venv/Scripts/pytest.exe`；系统 `python -m pytest` 没装 pytest。迭代时加 `--no-cov` 并指定具体文件；带覆盖率的全量套件约 15 分钟。
- 前端 `tsc --noEmit` **什么都不检查**（根 `tsconfig.json` 是 solution-style，`"files": []`）。真正的门是 `tsc -b`。
- mypy 必须带 CI 的 `--no-site-packages`，否则会报 numpy 存根里的 Python 3.12 语法错误。
- `gh` 读不了 git-bash 的 `/tmp`。PR body 写到 `C:\Users\24100\AppData\Local\Temp\`。
- CI 只在指向 `main` 的 PR 上跑；堆叠 PR 拿不到任何检查，且 ruff 会在 pytest 之前就让 backend job 挂掉。
- shell 的 cwd 在多次调用间持久。`cd` 到别处之后记得给命令加完整前缀。
- 用 Grep 工具而不是 shell `grep -rln` 全仓搜索；后者在本仓库会超时。

**改动约束**

- 迁移有**两条分叉路径**（文件库走 sync runner 的 `MIGRATION_POST_STEPS`；内存库逐个重放 `.sql` 且跳过 post-steps，靠 `app/core/database.py` 手工内联重放）。**加迁移要两边都改**，并更新 `tests/data/test_content_project_calibration_migrations.py` 里**四份**穷举版本列表。
- `next_best_actions.action_type` **有 CHECK 约束**。加动作类型用 `_expand_intent_action_types`（`runner.py`），别再各写一份；同时补齐 `HomePage.tsx` 的两个 `Record<IntentAction['action_type'], string>` 穷举表。
- capability 列表在 `creator_state.py` 和 `MePage.tsx` 各有一份，改要改两处。
- 绝对不要重新引入全局 `candidate_acceptance_rate` 或项目数作为资格条件（ADR 0002 明令禁止，仅可展示）。
- 不要删 `backend/data/` 下的本地数据库。
- 不要直接推 `main`；一律 feature 分支 + PR。`origin` 保持 `https://github.com/wu908/topicai.git`。
- 破坏性 git 操作（force push、`reset --hard`、`clean -f`、`branch -D`）需用户明确许可。

**排查经验**

- 测试里断言 `response.json()` 之前先断言 `status_code == 200, response.text`。否则服务端 500 会伪装成 `JSONDecodeError`。
- `codegraph_explore` 在本仓库查后端服务时会返回大量无关的前端结果（本轮实测：查 `_applicability` 调用点返回的是 `MaterialsPage.tsx` / `ContentPage.tsx` / `content.ts`，且把符号定位到 `creator_rule.py` 而不是 `content_genome.py` 的调用点）。查具体调用点用 Read/Grep 更快。

---

## Suggested skills

下一次开工按顺序用：

- `search-first` —— 动手之前先读回相关 spec 段落与既有代码（`CLAUDE.md` §2.3 要求）。第 4 节第 2 项尤其需要，因为要先判断走哪条修法。
- `tdd-workflow` —— 宪法 Principle II 是硬性要求：测试必须先失败。
- `verification-loop` —— 对照 `specs/007-v4-gap-closure/quickstart.md` 里的验收场景。
- `code-review` —— 一个逻辑组／user story 阶段完成后跑。
- `quality-gate` —— 宣布阶段完成之前跑。
- `database-migrations` —— 只要新建 `NNN_*.sql` 就用，并配合上面关于两条迁移路径的告警。
