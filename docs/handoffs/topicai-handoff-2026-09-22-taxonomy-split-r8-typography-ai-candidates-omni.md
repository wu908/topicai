# TopicAI Handoff — 2026-09-22 · 品类拆分 Step 1–3 上线 + 发布链路修复 + 排版五档 + AI 候选 + 音视频接入

状态：**本文覆盖的八个变更（PR #127–#134）已合并、部署并线上验证，服务器与
`origin/main` 停在 `e7f49f0`**。本文在 2026-09-22 汇总，工作发生在 2026-09-18 → 09-19。

> ⚠️ **同时存在并行会话的在途工作**（09-19 起，未提交）：`backend/app/services/reference_anchor.py`
> 及其测试、`frontend/src/pages/{Content,Home,Inbox,Materials,Onboarding,Urgent}`、`styles/globals.css`，
> 以及新文档 `docs/reviews/user-acceptance-test-2026-09-19.md`（**含修复进度**）、
> `docs/reviews/feature-inventory.md`、`docs/design/content-page/`、`docs/research/content-page-design-methods.md`。
> **接手前先读用户场景测试报告那一份**，它是当前活跃主线；提交时逐路径 `git status` 核对，
> 不要把在途改动一起扫进来。

> 本文只写"下一个会话需要知道、且别处查不到"的东西；具体实现、判据与踩坑细节都在
> PR 描述、commit message 与既有报告里，逐条给路径，不重复。

## 1. 本会话交付（按用户提出顺序）

| PR / commit | 内容 | 判据（怎么算验证过） | 细节在哪 |
|---|---|---|---|
| #127 `8985c01` | 品类拆分 **Step 1**：加开放字段 `content_form`（AI 命名"这条内容是什么"），纯管道零视觉变化 | 真实模型命名具体（30天养护记录 / 水彩作品展示）；迁移 057 同步进 043 重建 DDL | commit message |
| #128 `85c2011` | **Step 2**：展示层换位——卡片/列表/工作台先显示 AI 命名的形态，三值降级 | 线上 1280/390 走查；顺带修掉"动作标题副本"与视图契约不一致（StrictModel）两个真问题 | commit message |
| #129 `f3fd166` | **Step 3**：三值正名为**机器模式**（教方法/讲经历/记过程），字段改叫「处理方式」；急稿第 3 步从"属于哪一类"改为"AI 按哪种方式帮你" | 全量回归 + 线上走查 | 方案在 `docs/reviews/intent-taxonomy-split-migration-plan-2026-09-16.md` |
| #130 `90113b2` | **R8 修复**（线上报"点提炼候选 → 请求参数错误"）：见下方第 2 节的根因链 | 线上完整复现 → 修复后同一次调用 201；三条服务层回归 + 一条 API 文案测试，每条都回退验证过 | commit message |
| #131 `a01e58a` | **排版五档**：15 种字号 → 5 档（`--fs-*`）、中文负字距归零、MUI 浮动标签 10.5→12px | 实测档位数（工作台/产出架各 4 档）+ 双视口无溢出；工具 `frontend/scripts/type-scale-audit.mjs` | commit message |
| #132 `57d1244` | **结构化输出修复**：`generate_structured` 从不发 schema，5 个提示词静默降级 | 线上同一次调用 `proposal_source` 从 `deterministic_fallback` → `ai` | 本地记忆 `topicai-llm-structured-output` |
| #133 `77a2ea5` | **AI 候选**：六个可填字段进入面板即给 3 条候选（带理由），点一下填入、仍可任意改，AI 不可用给通用方向/骨架 | 线上 `source: ai` + 截图；后端 6 条契约测试 + 前端 6 条组件测试（含 StrictMode 只取一次） | commit message |
| #134 `e7f49f0` | **音视频素材识别**（小米全模态）：类型、尺寸、`OmniClient`、`POST /materials/{id}:analyze`、敏感不外发、来源可见、素材页入口 | 线上建音频素材 ✓；未配 key 时返回可读拒绝 ✓；后端 8 条契约测试（含"敏感素材绝不出网"） | `docs/reviews/omni-audio-video-integration-2026-09-18.md` |

回归总账（09-19 收尾时）：**后端 527 passed / ruff + mypy 干净；前端 288 passed / 44 文件 / tsc + eslint 干净；E2E 6/6。**

## 2. 两个"下次别再踩"的根因（本轮最有价值的两条）

1. **状态机"跳过提问" ≠ "意图已确认"**（#130）。`project_start` 把模型判断记进
   `start_inferred_intent` 并跳过重复确认，**却从没把意图落成已确认**，于是 `intent_status`
   永远是 `candidate`；而发布判断锁定、观点提炼、系列发现都要求 `working_confirmed` ——
   **走「开始一条内容」的项目根本走不完**，且拒绝是裸 `ValueError`，生产环境会把它的文案
   换成通用错误，所以用户只看到「请求参数无效」。修法：高/中置信度推断在创建时经
   `IntentConfirmationService` 落定；需要用户行动的拒绝一律用 `UserActionRequiredException`。
2. **同一个坑在多个调用点复发 = 边界少做了什么**（#132）。`generate_structured` 只让模型
   "返回符合 schema 的 JSON"却不发 schema，于是 5 个提示词各自静默降级；#85 的教训当时是
   逐提示词补 JSON 示例，这次改在边界上（由 pydantic 模型生成字段骨架塞进系统提示）。

## 3. 未完成 / 下一步（按优先序）

0. **当前活跃主线是并行会话的用户场景测试与修复**：`docs/reviews/user-acceptance-test-2026-09-19.md`
   的「1b. 修复进度」列了阻塞级 F1/F2/F25 与高中优先级 F3–F7 的处理状态；接手时以那份为准，
   本文下面几条是它之外仍挂着的。
1. **音视频识别还差一步就能真跑**：需要用户把 `OMNI_API_KEY` 写进服务器 `.env` 并设
   `OMNI_ENABLED=true` 后重新部署（key **不能经过对话**，由用户自己填）。配好后要做的：
   用一段真实音频跑端到端，确认识别文本落库、`analysis_json` 与 `ai_traces_v2`
   （`capability=omni_media`、`actual` 含 `external_model_read`）都对，再看是否需要调
   `fps`/时长上限。已知边界：base64 内联上限 40MB；更大的文件需要先有**公网可访问地址**
   （等暴露用户素材，属产品决策，未做）。
2. **素材页音视频入口的截图视觉确认**：本轮只做了 API 级线上验证 + 前端单测，
   没有对素材页做 1280/390 的视觉走查（用户的一贯要求是改页面必须看图）。
3. **拆分 Step 4**：仅当真的出现**第四种行为**才放宽那六张表的 CHECK；
   `intent_rubric` 里加一条即触发。方案见迁移方案文档第 5 节。
4. **逐页视觉抽查的剩余部分**：机会 / 素材 / 我的 / 成长 / 引导（第七轮只做了首屏与溢出
   检查，逐页判断仍挂账；`docs/reviews/page-visual-pass-2026-09-15.md` 有方法）。
5. **狗粮测试者开始测试**：`docs/dogfood/tester-brief-2026-09-15.md` 已在仓（含服务器地址），
   用户已招募；测试者反馈要按"第一性原理拆解意图、不要给选项"的方式处理。
6. **悬置项**（用户明确让先放着）：Mimosa 上游反馈（决策材料见
   `docs/reviews/mimosa-security-gate-decision-2026-09-15.md`）；参考样本的单条删除入口。

## 4. 环境与安全（必须遵守，违反会造成真实损失）

- **密钥永不进对话**：`.env` 里是真实凭据，只在服务器/本机填写与校验（可 grep 变量名）。
  临时改写过 `.env` 的脚本，退出前必须还原。
- **不用 `git add -A`**：显式列路径暂存（`git add -A` 曾扫入 167 个
  Mimosa 运行产物）。本会话每次提交前都 `git status --porcelain` 核对。
- **推送**：本机 git 走 `http.proxy=127.0.0.1:18780`，代理离线时全部失败而**直连可通**，
  绕法是 `git -c http.proxy= -c https.proxy= push ...`（不改配置）；GitHub 也会间歇性
  整体不可达，**循环重试即可**（本次曾 20+ 次失败后成功）。
- **服务器**：`ssh topicai-server`（专用密钥 `topicai_server_ed25519` + `known_hosts.topicai`；
  本机 `~/.ssh` 下旧文件被 ACL 锁死，不要动）。生产 `http://1.13.251.252:8081/`，`/opt/topicai`。
  **部署四步缺一不可**：①前台 `git pull` 并**核验 HEAD 等于目标 commit**；②`docker compose
  build`；③`up -d --force-recreate`；④**进容器核验代码**（`grep` 新符号 / 看前端产物）。
  本轮就靠第④步抓到过一次"漏拉一个 commit 导致前端产物是旧的"。
- **临时验收账号**：注册 → 用完**必须注销**（隐私门槛流程 `POST /account/deletion:request`
  → `human-gates/{id}:decide` → `DELETE /account?gate_id=`），注销后用户数应回到 **3**。
- **危险命令禁止**：`docker volume prune`、`docker system prune --volumes`、
  `docker compose down -v`（服务器上等于删数据）。
- **容器内跑脚本**：`python /tmp/x.py` 的 `sys.path[0]` 是 `/tmp`，
  需要 `-e PYTHONPATH=/app`（本轮踩过）。
- **前端/容器验证要走技能**：Docker Compose、全栈运行时验证请显式调用
  `$windows-wsl-docker-validation`，并读 `mvp/docs/agents/wsl-docker-development.md`。

## 5. 复现"已验证"要用的工具（都在仓里）

- `frontend/scripts/taxonomy-step2-shots.mjs` / `taxonomy-step3-shots.mjs`：双视口（1280/390）
  页面截图 + 溢出/越界体检。**两个坑写进脚本注释**：内容页 dev 冷加载约 6 秒才挂载（固定
  秒数会拍到空页，要等 `main` 里出现文字）；滚动容器是 `main`，必须等数据到齐后再滚。
- `frontend/scripts/type-scale-audit.mjs <路由>`：打印页面字号档位分布（判"层级乱不乱"的量化依据）。
- 本地栈：后端 `uvicorn main:create_app --factory --port 8765`；前端 `vite --port 5173`；
  走查令牌用 `AuthManager().create_access_token(<本地账号 id>)` 写到 `~/.topicai-loop-walk-token`。
- 截图目录 `browser-screenshots/`（不入库）：`taxonomy-step2/`、`taxonomy-step3/`、
  `type-scale/`、`field-suggestions/`。

## 6. 建议技能（下次会话）

- `$handoff`：每次会话收尾生成新交接文档（**用户要求存进项目文档**，即本目录，而非临时目录）。
- `$windows-wsl-docker-validation`：任何 Docker Compose / 容器内验证 / 全栈运行时确认。
- `$diagnosing-bugs` 或 `$diagnose`：本项目的用户反馈基本都值得走"完整复现 → 追到根因 →
  回退验证修复"（本轮 #130 就是这么找到"整条发布链被挡住"的）。
- `$code-review`：合并前对 diff 做一遍独立复审（本轮两个真问题都是靠自己复核而非测试发现的）。
- 视觉类任务：优先用 `documents:visual-judge` 系列的 `visual-judge` 子代理做验收
  （拿到渲染后的页面 PNG 再判），不要在写代码的会话里自评。

## 7. 下一个会话的第一件事

先读 `docs/reviews/user-acceptance-test-2026-09-19.md` 的「1b. 修复进度」，
接着做那份报告里尚未完成的修复（那是用户真实走查的结论，优先级高于本文其余条目）。
同时问用户 `OMNI_API_KEY` 是否已写入服务器 `.env`：

- **已写入** → 用一段真实音频（或视频）跑通 `POST /materials/{id}:analyze`，核对识别文本、
  `analysis_json`、`ai_traces_v2` 三处；然后对素材页做 1280/390 视觉走查（第 3 节第 2 条）。
- **未写入** → 直接进第 3 节第 4 条：逐页视觉抽查（机会 / 素材 / 我的 / 成长 / 引导），
  方法沿用 `docs/reviews/page-visual-pass-2026-09-15.md`：先量几何（重叠、越界、行分组）
  再看图判断，发现问题先给量化证据再改。

> 本交接文档由 AI 依据本地 Git 状态、PR #127–#134、GitHub Actions 结果、线上验收记录与
> 项目既有文档整理；未包含任何密钥或凭据。
