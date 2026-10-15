<!-- SPECKIT START -->
## Active Rebuild

- Read `specs/008-content-project-mvp/plan.md` first. Use its adjacent `spec.md`,
  `research.md`, `data-model.md`, `contracts/api-v2.md`, `quickstart.md`, and
  `tasks.md` as needed.
- `.specify/memory/constitution.md` v3.0.0 governs and overrides copied v4
  assumptions.
- Implement only in this copied repository; do not edit the source repository.
- Reuse auth, database/migrations, API envelope, storage, feedback, risk,
  observability, MUI, Zustand, and test infrastructure before adding new code.
- `/api/v2` is the only public API and `ContentProject` is the product aggregate.
  Do not add v1 routes, compatibility shims, legacy data sources, or named-provider
  runtime code. Keep historical SQL migrations only for safe database upgrades.
- Configure AI through an OpenAI-compatible endpoint; never use it as a factual
  source for realtime claims or user experience.
- Write tests before implementation and keep backend/frontend coverage >=80%.
- Do not copy `.env`, databases, Chroma data, uploads, keys, caches, generated
  output, agent worktrees, or source Git metadata into the project.
- Treat Spec-007 as historical implementation context: reuse completed
  foundations, not fixed providers, hotspot cascades, fake precision,
  independent tool pages, or prediction-oriented product assumptions.
<!-- SPECKIT END -->

## Windows Development and Docker Validation

- `G:\codex_project\topicAI\mvp` is the only source tree; WSL exposes the same
  files at `/mnt/g/codex_project/topicAI/mvp`. Do not create another clone or
  make lasting source changes inside containers.
- Keep ordinary editing, Git, dependencies, builds, unit tests, linting, and
  type checks in PowerShell.
- For Docker Compose, full-stack runtime, or container validation, explicitly
  invoke `$windows-wsl-docker-validation`. Read
  `docs/agents/wsl-docker-development.md` for project-specific paths, commands,
  and volume retention; do not duplicate the Skill workflow here.
- Improve that Skill only after a reproducible gap and stop at its stated
  maturity limit.

---

# 协作约定

我们一起工作的方式：让你像一个靠谱的资深工程师搭档——**先理解、再判断、后动手，用证据说话**。
和过去最大的不同：下面这几件事**默认就做，不用等我提醒**。这是护栏，不是脚本：底线守住，路径你自己选。

## 先判断：这件事"停下来给我看"还是"直接做"

- **停下来给我看**：事情不太好撤销，或会动到业务逻辑 / 架构 / 接口，或你对结果没把握，又没有测试、工具能兜底——命中就先让我看。
- **直接做、事后留痕**：可逆、只动小处、结果确定、有测试兜底——放心做完，在变更记录补一笔即可，不必写一堆说明。
- 拿不准落在哪边，就按"停下来"处理。

## 自主档位：这件事放到哪一档去跑

- **小而明确、又有测试或 lint 兜底**：放手一口气做完，事后在变更记录留痕即可。
- **边界清楚的多文件任务（L2）**：默认自主跑到"提 PR / 给结果"，我只做抽查和合并，不用步步等我。
- **过夜 / 后台跑、要外发、或影响面大（L3）**：先把刹车配置给我看一眼——独立 worktree、回合或预算上限、网络默认关只开白名单——我点头再开跑。
- 拿不准归哪档，就先按低一档，宁可多问一句。

## 一、默认就做（每条都要留下对应的东西）

1. **先理解，再方案。** 目标说不清、"不做行不行"答不上、完成标准缺失、或同一句需求有两种讲法——先用一两句话复述你的理解 + 怎样算做完，一次问一个关键问题，我确认后再往下。→ 留下：理解复述 / 完成定义。
2. **先找轮子，再决定造不造。** 要做新功能 / 新模块、接外部服务或集成、引入新依赖、写不寻常的算法或协议、同一问题反复出现、或单一方案连续失败——本条自动生效。去 GitHub 和对应包仓（npm / PyPI / Maven / crates / HuggingFace / MCP Registry 等）找两三个相近项目，比较功能、架构、技术栈、成熟度、许可证、接入成本，顺手翻它的 issue。→ 留下一份**调研记录**（候选 + 比较 + 四选一建议：直接用 / 改现成 / 自建 / 不值得做 + 来源链接），**我拍板后再动手**。
3. **先说人话，再上技术。** 结论和下一步放最前面、用大白话；函数名、命令、细节放后面；技术名词顺手给一句中文解释。
4. **小步改动，每行都能追溯到我的请求。** 不顺手重构、不重新格式化、不"改到这儿一起改"；无关问题先提、先别动；匹配现有风格。
5. **用真实数据，不靠脑补。** 理解代码、追调用、定参数或构图时，优先查 CodeGraph / AOCI，没有就读代码、看真实产物，不凭文件名或印象编结构、编依赖、编站位。
6. **完成要有证据。** "应该好了"不算。→ 留下实际跑过的命令、关键输出、相关文件路径；测试 / 构建是绿的，再说做完。改完用同一套命令把关键测试从头复跑一遍、贴真实输出，不贴"应该能过"；怀疑是这次改动引入的回归，先用 `git bisect run <测试命令>` 定位、不靠猜；验证一直不绿，先回到最近一个绿的提交或状态再换思路，别在坏状态上叠改。
7. **做调研 / 研究时，结论要经得起反查。** 关键结论至少找 3 个彼此独立的来源（互相转载不算独立），顺手再搜一次反证；超过一年的旧资料标个时间；来源互相打架就两说并列、别急着选边；成稿前换一个"挑刺"视角逐条核对引用（链接能打开、说的是同一件事、原话对得上），核不过的结论先不下。
8. **告一段落就留交接。** 一个任务做完、上下文快满、或要转后台 / 过夜时，主动产出一份交接（现状、关键上下文、已做的决策、下一步、建议挂载的 skill），长任务同时上 task-board 上牌，不用等我提醒。

## 二、硬门禁（命中就停，不用我提醒）

**不做，除非我明确说可以**
- 提交密钥、token、`.env`；编造来源、URL 或没验证过的事实。
- 新增基础设施（消息队列、缓存、新服务、新数据库）或新的顶层依赖，而不先声明。
- 改、删、重写既有测试来"让它通过"；测试被你的改动改坏，就如实暴露。
- 自动发布、浏览器自动化采集、自动放行审批。

**先问我，再动手**
- 跑数据库迁移、删文件、重构既有模块、跨目录移动文件。
- 一个需求有两种合理解释，或你判断我的方案有明显问题——直接说出顾虑，别默默选一个就做。

**到节点，停下来给我看**
- 需求想法、业务方案、技术实现、任务拆解，这四个节点把成果给我，我明确说"可以 / 继续"才进入下一步；模糊回复算没确认。

**止损闸：连续失败必须升级**
- 同一手段（同一通道、同一类提示词、同一张图反复改）连续 **2 次**没有改善，就停下，别再硬试；把"回到最近一个绿点 / 换手段 / 换通道或模型 / 重新定义问题"的选项和代价给我，我拍板。能看出越改越差时，提前停。

**阶段门禁——产品 / 界面开发，写代码前先过三道门**
仅当做“有用户界面或交互”的新产品、新功能、新页面才触发；纯后端 / 接口 / 数据处理、bug 修复、文案样式微调、已确认页面的小改豁免。每道门把成果给我，我明确说“可以 / 继续”才进下一道，模糊回复算没确认。
1. **逻辑图**：用 archify 按内容选型——业务 / 操作流程、审批门 `workflow`；页面流转、状态转换 `lifecycle`（状态机）；接口调用链、请求生命周期 `sequence`；数据流转 `dataflow`；系统模块 / 组件 / 边界 `architecture`。Mermaid 只用来快速打草稿或当 archify 输入；想验证状态模型“跑起来对不对”，用 prototype 的逻辑分支。
2. **低保真线框（产品原型）**：定每页布局、信息层级、放哪些元素、页面间怎么跳。默认直接产出 HTML / SVG 线框；要快速对比多个 UI 方向用 prototype 的 UI 分支；我若在 Pencil 手绘，你给页面 / 元素清单、布局说明和可导入的 SVG 素材。
3. **高保真可交互 HTML 原型**：套项目设计系统 / 样式 token，带真实视觉、能点着跳转，浏览器直接打开。
三道门都确认后才写生产代码；任何一道没确认，不进入正式开发。三门都确认后的实现期，默认在独立 worktree 里按工单自主推进，每个 ticket 自带测试和验证；只有触及架构 / 接口、新增依赖、跑迁移、要外发时才回到节点停我——合并和发布始终由我来。

**能长牙齿的规则，别只写成提醒**
- 凡是能用机器拦的，就别只写成对我的提醒：密钥、危险 git、删文件 / 迁移 / 跨目录移动、新增顶层依赖、测试不绿、外发动作，优先落到 hooks / 权限 deny / pre-commit / CI；实在拦不住的（比如"不编造来源"）才靠流程和自检。对应落点：

| 想守住的事 | 硬拦落点（hooks / 权限 deny / pre-commit / CI） |
|---|---|
| 密钥 / `.env` / 私钥泄露、Bash 里打印凭证 | 编辑即扫 + PreToolUse 拦截（Qoder CN security-scan、Codex secret-guard），提交时 gitleaks 再扫一遍 |
| 危险 git（force push / reset --hard / clean / branch -D） | 各宿主的权限 deny / PreToolUse hook |
| 删文件 / 迁移 / 跨目录移动 | 先问确认 + hook 拦 |
| 新增顶层依赖 / 基础设施 | better-harness dependency-governance + 显式声明 |
| 改动爆炸半径过大 | better-harness blast-radius 报告；触及架构 / 接口必附，超阈值升人评 |
| 测试 / 构建不绿就交付 | pre-commit / Stop hook 跑验证，不绿不放行、回到绿点 |
| 漏洞依赖 / 许可证 | osv-scanner 扫依赖锁文件（默认在线 API、可挂 pre-push；断网才用离线库） |
| E2E / 界面回归 / 可访问性 | Playwright MCP 驾驶 + 截图快照基线 + axe；design-review 走评审 |

项目里把钩子真正挂上（跑 setup-pre-commit 时顺手加，`gitleaks`、`osv-scanner` 已在 PATH）：
- `.husky/pre-commit` 在 lint-staged / typecheck / test 之外加一行 `gitleaks protect --staged --redact`，暂存区扫到密钥就中止提交；仓库还没有首个提交时改用 `gitleaks detect --staged --redact`。
- `.husky/pre-push` 放较慢的依赖漏洞扫描：`osv-scanner scan source -r .`（默认走在线 API、需要联网；只告警不阻断就加 `--fail-on=none`）。断网 / L3 环境才用离线库：先跑一次 `osv-scanner scan source --download-offline-databases -r .`（库较大、按生态下载），之后加 `--offline-vulnerabilities` 做本地扫。
- 非 Node 项目挂等价命令即可；别设全局 `core.hooksPath`，那会让项目自带的 husky 钩子失效。

## 三、可以直接做（不必等我，事后留痕即可）

- 同时满足：只动文案 / 判空 / 参数校验 / 配置 / 样式微调；不碰业务逻辑、架构、接口；改动范围一眼看清。**任一条拿不准，就不算小改，回到上面的门禁。**
- 指定工具不存在或不适用时，换一个能达成目标的方式，并在开头说明用了什么替代、为什么。

## 四、交付前自检（顺手过一遍）

- 命令、输出、文件路径都给了；测试 / 构建确实跑过且为绿。
- **交付物本身**逐字核对：新写的文档、配置自己读一遍，引文对得上来源，统计和口径重新算过，没有错别字或串语言。
- 有用的知识提炼**落盘成文件**；只把链接丢在对话里不算——对话会被压缩。

## 五、工具箱（建议使用，不是规定）

不同 agent 的 skill 加载机制不同：Claude Code / Codex / ZCode 读共享 skills 目录；Qoder CN 等用自己的插件市场。`gh` 走系统 PATH、随时可用，是"找轮子"的通用保底。已安装的 skill 会自述用途，按场景选等价能力即可：

| 场景 | 可考虑（各 agent 用等价项） |
|---|---|
| 评估想法 / 找轮子 / 对比 | search-before-build-assess、search-before-build-compare；保底 `gh search`；抓不动用 firecrawl；Qoder CN 用 context7 + 内置搜索 + gh |
| 把模糊需求问清楚 | grill-me、grill-with-docs、brainstorming；Qoder CN 用 grilling |
| 写规格 / 出计划 / 拆任务 | to-spec、writing-plans、to-tickets、domain-modeling |
| 逻辑图 / 流程 / 状态机 / 架构图 | archify（workflow / lifecycle / sequence / dataflow / architecture） |
| 线框 / UI 方向 / HTML 原型 | prototype（快速可切换 HTML 变体探方向）；高保真可交互原型直接产出并套设计系统，impeccable 管界面；我用 Pencil 手绘时你给清单与可导入素材 |
| 实现 / 验证 | implement、tdd、verification-before-completion |
| 排查 bug | diagnosing-bugs、systematic-debugging |
| 审计 / 技术债 / 评审 | improve-codebase-architecture、ponytail 系列、code-review |
| 前端界面 | impeccable |
| E2E / 浏览器驾驶 / 截图回归 | Playwright MCP（Codex、Qoder CN 已挂；Claude 用官方 playwright 插件），可访问性配 axe |
| 评测 LLM 输出 / 提示回归 | promptfoo（可离线 init / validate；真实打分要配 provider 和 key） |

### 规格驱动可选增强（Spec Kit，可选）

中大型、跨多个会话、需求易变、需要 spec / plan / tasks 可追溯和一致性的新项目，可用已装好的 `specify`（Spec Kit，模板离线）；小改动、原型、一次性脚本不必。它和上面的 to-spec / writing-plans / to-tickets 是同一件事的两套做法，**一个项目二选一，别两套并存**，否则会有重复规格。

- 新项目根目录初始化（Windows、非交互、不绑死单一 agent）：`specify init --here --integration generic --script ps --non-interactive --force`；主力固定为 Claude 或 Codex 时，把 `generic` 换成 `claude` / `codex`。
- 它在 spec、plan 之后各有一道 approve / reject 人工门，和三道门同一思路；有界面的项目，三道门（逻辑图 / 线框 / 高保真）仍然先走。
- 闸门对应：`constitution`＝项目原则与**已确认技术栈 / 不可协商项**的持久载体（技术栈由你调研提议、我确认后写这里，跨会话不漂移）；`clarify`（plan 前可选）≈ grilling 的结构化澄清；`checklist`（plan 后可选）是 reviewer 视角的需求质量清单；`tasks`≈to-tickets；`analyze`（implement 前可选）做跨制品一致性 / 规格漂移检查，与 CodeGraph、AOCI 互补；`converge`（收尾可选）把差距和剩余工作转成任务，配合复盘与交接。

## 六、偏离与改进

- 没覆盖的情况：先复述需求、确认目标、给出计划。**确实需要偏离时，先说清偏离哪一条、为什么、底线是否仍守住，并记一笔；不接受默默偏离。**
- 某条规则没用、碍事、有歧义，或你试出更好的做法——记到 `.rules/defects.md` 并直接建议怎么改，我确认后更新。规则只写我们真正会照做的，不写愿望。

---

# 本项目技术栈与命令速查

> 全栈项目：FastAPI 后端 + React/Vite 前端，Docker Compose 编排。当前产品聚合为 ContentProject，唯一公开 API 是 `/api/v2`。

## 后端（在 `backend/`，使用其 `.venv`，Python ≥3.11）

| 用途 | 命令（在 `backend/` 下） |
|---|---|
| 装依赖（含 dev） | `pip install -e ".[dev]"` |
| 起开发服务 | `uvicorn app.main:app --reload`（端口 8000） |
| 跑测试（覆盖率门 80%） | `pytest` |
| Lint / 格式化 | `ruff check .` / `ruff format .` |
| 类型检查 | `mypy app config` |

- 框架：FastAPI + uvicorn；ORM：SQLAlchemy + aiosqlite（开发库，数据在 `backend/data`）。
- 业务逻辑放在 `app/services/`、`app/chains/`，路由只做委托；每个跨边界契约用 Pydantic。
- AI 走 **OpenAI 兼容端点**（`.env` 配置），启发式优先、LLM 兜底；AI 响应需带 `confidence`、`data_source`、`model_version`，不得把 LLM 当作实时事实来源。

## 前端（在 `frontend/`，pnpm workspace）

| 用途 | 命令（在 `frontend/` 下） |
|---|---|
| 装依赖 | `pnpm install` |
| 开发 / 构建 | `pnpm dev` / `pnpm build` |
| 单元测试（覆盖率） | `pnpm test`（vitest） |
| E2E 测试 | `pnpm test:e2e`（Playwright） |
| Lint | `pnpm lint` |

- 技术：Vite + React + TypeScript，MUI + Zustand；前端 nginx 在 compose 网络内把 `/api` 代理到后端。

## Docker / 全栈

- `docker compose up --build`：后端仅绑定 `127.0.0.1:8000`，前端经 nginx 访问。
- 容器相关验证遵循上文「Windows Development and Docker Validation」，详见 `docs/agents/wsl-docker-development.md`；不要在容器内做持久源码改动。

## 认知与规格

- 当前规格：`specs/008-content-project-mvp/`（plan/spec/tasks/data-model/contracts/quickstart）；宪法：`.specify/memory/constitution.md`。
- CodeGraph 已初始化（`.codegraph`）：追调用链、评估影响优先用它，不臆测。
