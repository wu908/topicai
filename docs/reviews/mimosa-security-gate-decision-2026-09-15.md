# Mimosa 安全门决策材料（2026-09-15 调查）

> 触发：需要决定这道安全门是保持关闭、改代码去适配它、还是上游报问题。
> 本文只整理**可验证的事实**与三个选项的代价，结论留给你拍。
> 所有数据来自本机实际文件（`.mimosa/`、`~/.mimosa/`、插件包）与实际执行的扫描命令。

---

## 一、现状

- **插件当前是关闭的**：`~/.zcode/cli/config.json` 里
  `plugins.enabledPlugins["mimosa@zcode-plugins-official"] = false`，
  备份在 `config.json.bak-mimosa`（唯一差异就是这个开关，`hooks` 段未动）。
- 安装版本 1.0.3。
- **仓库里没有装原生 git hook**：`.git/hooks/` 只有 `*.sample`，`core.hooksPath` 未设，
  `.git/config` 里没有 mimosa 配置。
- 也就是说：当初拦住 `git commit` 的**不是 git hook，而是 ZCode 的 agent 层 hook**
  （插件用 `PreToolUse matcher: "Bash"` 拦截 shell 命令）。这解释了为什么 `--no-verify` 没用
  ——它拦的是"执行 git 命令这个动作"，不是 git 自身的 hook 阶段。

## 二、它一共挂了 6 个 hook（来自插件 `hooks/hooks.json`）

| 事件 | 匹配 | 作用 |
|---|---|---|
| PreToolUse | `Edit\|Write\|MultiEdit` | 写入前扫描候选代码，可 **deny** |
| PreToolUse | `Bash` | 命令与 Git 门禁（拦 commit/push），可 **deny** |
| PostToolUse | 同上两类 | 写入后复查 |
| UserPromptSubmit | — | 提示词层 |
| SessionStart | — | 项目安全上下文 |
| Stop | — | 一轮结束复查改动 |

门禁档位（`contracts/scan-profiles.json`）：`diff-only`、禁网络、禁 LLM、禁 semgrep、
PreToolUse **硬超时 1 秒**。所以规则是内置的模式匹配，**规则包是密封的**
（`dist/cli.js` 只有 586 字节的加载壳，真正的实现在 `*.mimosa` + `protected-loader.cjs`）。

## 三、它到底报了什么（有据可查的部分）

密封深扫（`~/.mimosa/security-scans/.../report.md`，2026-09-13，覆盖 264 个文件、
`completeness: complete`）报了 **6 条 HIGH**，`Verdict effect: none`（深扫只报不拦）：

| # | 位置 | 类型 | 今天的状态 |
|---|---|---|---|
| 1 | `frontend/playwright.config.ts:60` | 硬编码凭据 | **已真修**：现在是 `e2e-secret-key-${Date.now()}`，每次运行唯一 |
| 2 | `runner.py:112` | SQL 拼接 | **已真修**：换成参数化 `SELECT name FROM pragma_table_info(?)`；Mimosa 自己也记录了 `static_fix_verified` |
| 3 | `runner.py:149` | SQL 拼接 | **仍在**（今天第 176 行 `ALTER TABLE {table} ADD COLUMN {name} {ddl_type}`） |
| 4 | `runner.py:317` | SQL 拼接 | **仍在**（今天第 344 行 PRAGMA，可同法修） |
| 5 | `runner.py:324` | SQL 拼接 | **仍在**（今天第 351 行 `DROP TABLE {table}`） |
| 6 | `runner.py:325` | SQL 拼接 | **仍在**（今天第 352 行 `RENAME TO {table}`） |

hook 账本（`.mimosa/finding-ledger/`）记录的是另一次：`runner.py` 两条 finding，
一条 `finding_blocked`，修复后一条 `static_fix_verified`。

> **更正（2026-09-15 决定后复核）**：上表第 4 行说"今天第 344 行 PRAGMA，可同法修"——
> 我已经把它改掉了（`_table_columns` 复用参数化写法）。但**当时"剩 4 处"是低估**：
> 我按 `execute(f"` 字符串 grep，漏掉了多行拼接的 f-string 和另外三个重建块。
> 用 Mimosa 自己的扫描器复核，这个文件里被报的位置是 **8–9 处**，准确分类见第四节末。

**当前项目安全状态**（`mimosa status` 实测）：
`total=2 · blocked=1 · fixed_static=1 · open=0`，总体"需要处理 · evidence=partial"。

## 四、决定性实验：这些发现能不能靠改代码通过

用插件自带 CLI（**不需要启用插件就能用**）对三种写法做 `scan --stdin python`：

| 写法 | 结果 |
|---|---|
| `conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}")` | ✗ 高危 SQL 注入 |
| 标识符校验 + 引号包裹后**字符串拼接** | ✗ 高危 SQL 注入（换了一条规则命中，"用户输入被直接拼接进 SQL"） |
| 参数化 `SELECT name FROM pragma_table_info(?)` | ✓ **未发现风险** |

结论（这次是实测，不是推测）：
1. **能参数化的地方有正解**——PRAGMA 那条就是，而且已经这么修好了。
2. **标识符进 DDL 的地方没有能通过的写法**：SQLite 不允许参数化表名/列名，而 f-string 与
   "校验后拼接"都被判高危。要让这三处通过，只能把动态 DDL 拆成一条条字面量语句
   （`ALTER TABLE "effect_reviews" ADD COLUMN ...` 逐条写死）或给每张表各写一份重建流程——
   可行，但把数据驱动的列表换成重复字面量，是**用可维护性换门禁通过**。

### `runner.py` 被报位置的准确清单（2026-09-15 用扫描器逐行复核）

| 类 | 位置 | 形态 | 能否通过 |
|---|---|---|---|
| A. 标识符进 DDL | 185 | `ALTER TABLE {table} ADD COLUMN {name} {ddl_type}` | **不能**（SQLite 无法参数化标识符） |
| A | 358 / 359 | `DROP TABLE {table}` / `ALTER TABLE {new_table} RENAME TO {table}` | **不能** |
| B. 运行时列名拼进 INSERT | 354-356 / 532-534 / 678-680 / 805-807 | `INSERT INTO {new} ({column_list}) SELECT {column_list} FROM {old}`（四处重建块） | **不能**：列名由 `PRAGMA table_info` 在运行时读出（列集随旧库版本变），改成字面量就得放弃"按实际存在的列拷贝"这一语义 |
| C. 把 SQL 常量交给变量再 execute | 351 / 526 / 365 | `conn.execute(replacement_sql)`、`conn.execute(statement)`（遍历字面量列表） | 这是**规则的形状误报**：SQL 文本本身是模块级字面量常量，没有任何插值 |
| — | 529 / 675 / 802 / 836 | `PRAGMA table_info(next_best_actions)` 等**字面量**表名 | 未被报（印证规则针对"动态构造"而非 PRAGMA 本身） |

也就是说：这个文件的迁移架构（按旧库实际列集做 12 步重建）与这条规则的根本冲突不止 3 处，
而是 A 类 3 处 + B 类 4 处；C 类 3 处则属于误报。

## 五、有没有"豁免"机制（这是决策的关键）

查证结果：**没有可用的 finding 级豁免**。

- 插件包、manifest、contracts 里 `allowlist|whitelist|suppress|waiver|baseline|exclude`
  **零命中**；`plugin.json` 的 `userConfig` 只有 `engine` 一项。
- 官方 README 列出的开关只有：`MIMOSA_HOOK_FAILURE_MODE=open|strict`、
  `MIMOSA_GIT_GATE_FAILURE_MODE=open|strict`、`MIMOSA_HOOK_STATUS=quiet|important|all`、
  `MIMOSA_HOOK_PROJECT=1`（非阻断提示）。**没有一条是"这条不算"**。
- 有一个项目级 `security-policy.json`（`mimosa policy init`），含 `threatModel.exclusions`。
  **实测**：把文件路径放进 `exclusions`（字符串数组）策略合法，但 SQL 高危**照报**；
  换成对象形状则策略被判"无效"，而**无效策略本身就是一条 HIGH**（CWE-693）。
  官方 policy 帮助里那句"用户可控的 SSRF、注入和 IDOR 仍会照常检测"与此一致。
- `backlog triage` 明确"不会自动标为 dismissed"；`validate` 需要 Key（本机显示"未复核(无 Key)"）。

## 六、它自身的可靠性问题（会影响"值不值得开"的判断）

- **Stop 复查路径在本机是坏的**：3 次运行全部 `runStatus: inconclusive`，
  `scanned_files: 0 / failed_files: 6`，`rulesVersion: unavailable`，
  原因是 `.pytest_cache`、`.ci-tmp` 等目录 `EPERM`（本机 ACL 锁死）导致 baseline 不完整。
  也就是说"任务收尾复查"这道防线当时**并没有真正在工作**，而它只在 `.mimosa/` 里留了记录，
  没有把这件事推到用户面前。
- **状态工具会因项目外文件报错**：`mimosa status` 输出了
  `✗ sess_....json：file 不是项目相对路径`（因为我编辑过仓库外的记忆文件，PostToolUse
  也扫了它）。小问题，但说明它对项目外文件的处理不完整。
- **规则的判定理由不可读**：账本里 `ruleId` 只有笼统的 `security`，没有具体规则名可查；
  规则包密封，所以遇到误报时**你无法在本地自证**，也无法查规则依据。

## 七、三个选项

### 选项 A：保持关闭（现状）
- 你仍然能用它的**全部扫描能力**，因为 CLI/深扫不依赖插件启用（本文的实验就是这么做的）：
  `mimosa scan <file|dir>`、`mimosa audit`、`mimosa security-scan run`。
- 代价：没有"写入前拦截"和"提交门禁"，安全判断要靠人主动跑。
- 适合：现在这个阶段（单人开发、CI 已绿、发布流程有自己的人工门）。

### 选项 B：开启，并把代码改到能过
- 需要做的事：把 `runner.py` 里 3 处标识符 DDL 拆成字面量语句（PRAGMA 那处照 `_existing_columns` 的写法改）；
  然后再开、再撞其他文件的规则——**门禁报过的条数比密封深扫多**，那些额外的条目我没有留存证据，
  所以"改完就一定能过"无法事先保证。
- 代价：可维护性下降；且在没有豁免机制的前提下，未来任何动态 SQL 需求都会再次撞门。
- 适合：如果你要把它当成长期强制门禁。

### 选项 C：上游报问题 / 等新版
- 可报的具体问题有三条，都是可复现的：
  1. 标识符进 DDL（SQLite 无法参数化）被判高危，且**没有豁免路径** → 建议提供 finding 级 waiver 或
     "已校验标识符"识别；
  2. Stop 复查在 baseline `EPERM` 时静默 `inconclusive`（扫 0 个文件）却不提示用户；
  3. `mimosa status` 遇到项目外文件的 hook-status 记录直接报错。
- 代价：等；收益：可能一次性解决"没有豁免"这个根本矛盾。
- 我没有找到本地市场源（`zcode-plugins`）或版本仓库，所以**报问题的渠道需要你确认**
  （ZCode 官方市场/插件页，或厂商提供的反馈入口）。

## 八、我的建议

**短期选 A**：把它当"按需审计工具"而不是"强制门禁"——能力全都在，且不阻断开发。
**同时做两件低成本的事**：
1. 把 `runner.py` 剩下那处 PRAGMA（今天 344 行）按已验证的写法改成参数化（有正解就该改，与门禁无关）；
2. 把上面三条可复现问题报给上游（尤其"没有豁免路径"这条——它是所有摩擦的根源）。

**若将来要开成强制门禁**，先解决豁免问题再开；否则每次合法的动态 SQL 都要为它改架构。

## 九、我无法确认的（如实列出）

1. 当初门禁在提交时"报了 16 条"这个数字：**没有留存的可查产物**（git 门禁的记录没落到
   `.mimosa/` 或 `~/.mimosa/`）。可查的是密封深扫 6 条 + hook 账本 2 条。
2. `threatModel.exclusions` 的**真实语义**：实现密封、文档未写，实测未观察到豁免效果，
   但也不能排除它只在别的路径（如 threat-model 校验）生效。要确认只能问厂商。
3. 是否有更新版本已修上述问题：本机缓存只有 1.0.3。

---

## 十、已决定的处置（2026-09-15：选 A）

**决定：门禁保持关闭**，把它当按需审计工具用。已执行两件事：

1. **把唯一能参数化的那处改掉了**：`runner.py` 的 `PRAGMA table_info({table})` 换成
   共用助手 `_table_columns()`（表值 PRAGMA + 绑定参数），`_existing_columns()` 复用它。
   这是与门禁无关就该那么写的改法（减少一处字符串构造），全量后端 492 passed。
   **注意**：它并没有让这个文件"过门禁"——A 类 3 处与 B 类 4 处仍在（见第四节清单）。
2. **整理出可直接发出去的报障文本**（四条都可复现，附命令与日志证据）：

> **Report 1 — 没有 finding 级豁免，导致合法动态 SQL 无法通过门禁**
> 项目里存在 SQLite 迁移重建逻辑：标识符（表名/列名）必须动态构造，因为 SQLite 不支持
> 参数化标识符。实测三种写法：`execute(f"ALTER TABLE {table} ...")` 判高危；
> **标识符校验 + 引号包裹后字符串拼接也判高危**；参数化 `SELECT name FROM pragma_table_info(?)`
> 通过。结果是这类代码无论怎么写都过不了 PreToolUse 门禁，而包内没有任何减免机制
> （`allowlist|whitelist|suppress|waiver|baseline|exclude` 在插件包内零命中；
> `plugin.json` 的 `userConfig` 只有 `engine`；文档开关只有
> `MIMOSA_HOOK_FAILURE_MODE` / `MIMOSA_GIT_GATE_FAILURE_MODE` / `MIMOSA_HOOK_STATUS` / `MIMOSA_HOOK_PROJECT`）。
> **期望**：提供 finding 级 waiver（按规则+文件+理由），或识别"已校验标识符"的写法。
>
> **Report 2 — `threatModel.exclusions` 语义未文档化，且填错会让策略失效并被判高危**
> `mimosa policy init` 生成的 `security-policy.json` 含 `threatModel.exclusions`，但无任何文档说明
> 其字段形状。实测：`["a.py"]` 形式策略合法，但被报的高危**照报**；改成对象形式
> （`{"path": ...}` / `{"file":...,"rule":...}` / `{"ruleId":...,"path":...}`）则策略被判"无效"，
> 而**无效策略本身是一条 HIGH（CWE-693）**。**期望**：补文档说明字段语义，或明确它不用于抑制 finding。
>
> **Report 3 — Stop 复查静默失败：scan worker 连续 `spawnSync … ETIMEDOUT`，扫 0 个文件却不提示用户**
> 本机连续 3 次 Stop 复查都是 `runStatus=inconclusive`、`scanned_files: 0 / failed_files: 6`、
> `rulesVersion: unavailable`，用户侧无任何提示——"任务收尾复查"这道防线等于没在工作却不为人知。
> **根因在 `~/.zcode/mimosa-debug.log` 里写得比 `.mimosa/` 报告更直接**：
> ```
> [stop-hook] file=.../async-loop.spec.ts scan=empty status=? error=spawnSync G:\nodejs\node.exe ETIMEDOUT
> ```
> 六个文件连续同一错误：scan worker 经 `spawnSync` 调本机 node 超时，于是
> `findings=0 status=inconclusive`。（同一次运行里 baseline 枚举另有 4 处 `EPERM`
> ——`.pytest_cache`、`.ci-tmp` 等本机 ACL 保护目录——两者叠加。）
> **期望**：①worker 超时不能当作"干净"，要显式告警；②`spawnSync` 的超时/重试可配置，
> 或在 node 路径可疑时给出诊断（`mimosa doctor` 目前未提示这一点）。
>
> **Report 4 — 项目外文件的 hook 记录会让 `mimosa status` 报错**
> 编辑仓库外的文件（例如用户级记忆文件）时，PostToolUse 照扫并写入 hook-status 记录
> （日志可见 `file=C:\Users\...\memories\...md outcome=clear coverage=complete`），
> 随后 `mimosa status` 直接报 `✗ …：file 不是项目相对路径`。
> **期望**：要么不记录项目外文件，要么 status 容忍并跳过。

### 投递渠道：查证结果（没有厂商直投通道）

把能找的地方都找了，结论是**这份插件没有对外声明的反馈入口**：

| 检查点 | 结果 |
|---|---|
| 插件包内所有文件 | **零个 URL**（`commands/`、`skills/`、README 中英版全查） |
| `.zcode-plugin/plugin.json` / `.claude-plugin/plugin.json` | 只有 name/version/description/author/license/keywords/commands/skills/userConfig/**mcpServers**，**无 homepage / repository / bugs / contact** |
| 官方市场清单（`cdn-zcode.z.ai/zcode/official-plugin/marketplace.json`，19 个条目） | mimosa 条目只有 `name / source(zip) / displayName / icon / description / version / author{name:"Mimosa"} / category / keywords` —— **同样没有任何支持字段**；19 个条目全都只有 `author` |
| 市场本身 | owner 是 **z.ai**（`https://z.ai`），即 ZCode 官方的插件市场，mimosa 由该市场以 zip 分发 |
| 插件自带的 `knowledge` 通道 | `knowledge health`：**unavailable**（storage/contract/scenarios 全 unknown）；`outbox` 对我们这两条 finding 直接 `skip`（`unsupported_status` / `source_batch_incomplete`），`items=0`，且 `network=false · publish-authorized=false` |

**所以能落地的只有两条路：**
1. **走 ZCode 官方反馈**（应用内反馈 / 官方支持渠道）——因为 mimosa 是 ZCode 官方市场里的插件、
   市场归 z.ai，权威接收方就是 ZCode/z.ai 自己。把第十节的四段文本整段贴过去即可（已写成自包含、
   带复现命令与日志证据）。本机未发现任何 ZCode 反馈页 URL，所以具体入口需要你从应用里找。
2. **留在自有仓库**（本文件）作为记录——选项 A 下它不阻断任何开发，所以"今天不发"不会丢东西。

## 十一、按需使用（选项 A 的日常操作）

扫描能力不依赖插件启用，需要时直接跑：

```bash
MIMOSA="$HOME/.zcode/cli/plugins/cache/zcode-plugins-official/mimosa/1.0.3/payload/dist/cli.js"
node "$MIMOSA" scan <file|dir>        # 单文件/目录静态扫描
node "$MIMOSA" audit <dir>            # 分级项目审计
node "$MIMOSA" security-scan run <dir> # 密封深扫（产出报告到 ~/.mimosa）
node "$MIMOSA" status --project <dir> # 当前项目安全状态与 finding 台账
```

**已接受的风险（有意保留）**：`runner.py` 的 A 类 3 处 + B 类 4 处会持续被报为高危；
原因是迁移架构必须动态构造标识符/SQL 文本，而门禁没有豁免路径。
一旦将来要把它开成强制门禁，先解决"没有豁免"这件事，否则每次合理的动态 SQL 都要改架构。
