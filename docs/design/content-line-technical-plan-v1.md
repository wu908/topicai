# TopicAI 内容线 · 技术实现方案 v1

> **状态**：技术实现节点（待你确认后进入任务拆解）  
> **日期**：2026-10-11  
> **上游**：业务方案 v1.1 · 交互 UI v1 · 功能盘点 · 改造骨架  
> **约束**：`/api/v2` only · additive migration · TDD 覆盖 ≥80% · 无死路降级 · 不在本稿写产品代码

---

## 0. 总架构（与现状对齐）

```
frontend (React/Vite/MUI)
  pages: Today / Content / Review / Path / Materials / Me
  features/content: ChatThread, ConfirmCard, *Pane, BenchmarkReader, ...
        ↓ /api/v2
backend FastAPI
  api/v2 (薄路由) → services/ (业务)
  chains/ + prompts/ (LLM) → OpenAI-compatible
  app/skills/  ← 新增：垂直技能编排（发现/成稿/产出/门禁/归因）
  SQLite + migrations 059+
  AITrace / HumanGate 保留
```

**复用优先**：Auth、Materials、Evidence、PublishCheck、HumanGate、AITrace、ReferenceAnchor、ProjectStart、async_loop（预产）、idempotency、ProjectStateEvent。

---

## 1. 数据模型（additive，建议 migration 059–063）

### 1.1 新表 / 扩展

| 实体 | 表 | 要点 | 迁移 |
|---|---|---|---|
| **PathProfile** | `path_profiles` | owner、statement、boundaries、cadence、style、status | 059 |
| **BenchmarkRead** | `benchmark_reads` | owner、samples_json、links、draft_json、confirmed_json、version | 060（可扩 `reference_anchors` 亦可独立；**建议独立**以免拖垮 R7 契约） |
| **FormulaNote** | `formula_notes` | owner、body、source（proposal/confirmed）、diff、version | 061 |
| **ContentBet** | `content_bets` | project_id、statement、locked_at、immutable 段 | 062 |
| **RetroSummary** | `retro_summaries` | project_id、metrics_json、ai_summary、accurate/biased 标记 | 062 |
| **ConfirmCard** | `confirm_cards` | unified type、payload、decision、reason、replaces HumanGate UI 映射 | 063 |
| **MaterialGap / Match** | `material_gaps` `material_matches` | project_id、need_list、matched_material_ids | 060 |
| **VideoPackage** | `video_packages` | project_id、shots_json、matched、assemble_status、srt、cover | 061 |
| **LearningSignal** | `learning_signals` | decision、edit_diff、retro_delta、skip_reason | 062 |
| **CapabilityTrust** | 扩 `creator_state` | per-action accepted count（对齐 Spec-012） | 063 |

### 1.2 扩列（非破坏）

| 表 | 加列 |
|---|---|
| `content_projects` | `content_kind` (`graphic_note`\|`vlog`), `path_profile_id`, `exploration_slot` bool |
| `content_versions` | `humanized` bool, `humanize_trace_id` |
| 现有 HumanGate | 映射到 ConfirmCard 类型（不删 gate 表） |

### 1.3 不动

Evidence、Publication、PublishCheck、Observation（入口冻）、CreatorRule/Viewpoint/Series（数据留）。

---

## 2. API 契约（`/api/v2`，增量）

### 2.1 新增（REST 风格与现有一致）

| Method | Path | 用途 |
|---|---|---|
| GET/POST | `/path-profile` | 画像读写（expected_version） |
| POST | `/path-profile:propose-revision` | AI 修订提案 |
| GET/POST | `/benchmark-reads` | 对标导入/查询 |
| POST | `/benchmark-reads:confirm` | 逐条确认解读 |
| GET/POST | `/formula-notes` | 公式笔记 |
| POST | `/formula-notes/{id}:decide` | 收/拒 |
| POST | `/projects/{id}/bets` | 锁 bet |
| GET | `/projects/{id}/retro` | 对账摘要 |
| POST | `/projects/{id}/retro` | 回填 1–2 数 / unknown |
| POST | `/projects/{id}/material-gaps` | 素材规划 |
| POST | `/projects/{id}/material-matches` | 匹配推荐 |
| POST | `/projects/{id}/video-packages` | 建视频包 |
| POST | `/video-packages/{id}:assemble` | 粗拼 |
| POST | `/confirm-cards/{id}:decide` | 同意/改/否决 |
| GET | `/today/queue` | 待决队列（或扩展 `/today`） |
| POST | `/content:humanize` | 内嵌人话化（亦可服务内调用不暴露） |

### 2.2 复用

`/projects`、`/materials`、`/publish-checks`、`/human-gates`、`/ai-traces`、`/reference-anchor`（兼容只读或别名）。

### 2.3 契约纪律

- 写操作：`idempotency_key` + `expected_version`  
- AI 输出：`confidence` / `data_source` / `model_version`  
- 错误 envelope 与现 `ApiResponse` 一致  
- **不**新增 v1；**不**破坏既有字段

---

## 3. 后端模块划分

### 3.1 新增 `app/skills/`（垂直技能，纯服务层）

| 模块 | 职责 | 依赖 |
|---|---|---|
| `discover.py` | 选题深挖、对标解读、素材缺口 | ReferenceAnchor/LLM |
| `draft.py` | 起草、改写、人话化、素材匹配 | Materials, LLM |
| `produce.py` | 视频脚本、粗拼编排 | ffmpeg 子进程/后续 |
| `gate.py` | 发前检查聚合、一键修、时机、bet | PublishCheck |
| `attribute.py` | 对账、准/偏、沉淀提案 | Snapshot/BlindReview 包装 |
| `orchestrator.py` | 七步状态、待决队列、确认卡投递 | IntentActions 可包装 |

**原则**：skills 不直接开路由；`api/v2` 薄委托；与现有 `services/` 事务边界一致。

### 3.2 改造点

| 现服务 | 动作 |
|---|---|
| `content_project.py` | 支持 kind/path_id |
| `intent_orchestrator.py` | 产出改为「对话步骤」数据，而非表单 next_action 枚举堆叠（保留字段兼容） |
| `publish_check.py` | 聚合一键修建议 |
| `reference_anchor.py` | 保留；BenchmarkRead 并行新实现 |
| `async_loop.py` | **预产**：后台可产 Draft 草案，状态 `prepared`，仅作加速 |

### 3.3 LLM / 去 AI 味

- 新 `prompts/humanize_*.md`：保事实/不删判断/长文保守（对齐 shuorenhua 三档）  
- 人话化默认服务内 post-process，可 `humanize=false`  
- 仍启发式优先、LLM 兜底；超时不阻塞手动路径

### 3.4 视频粗拼

- Phase P2.5：**先契约与任务态**，`assemble` 调本地 `ffmpeg`（若无则返回可下载 EDL/剪辑清单降级）  
- 不引入重型媒体依赖进默认镜像（对齐 Docker 瘦身历史）

---

## 4. 前端结构

### 4.1 目录

```
frontend/src/
  pages/Today/          # 新
  pages/Content/        # 重构：List + ProjectStage
  pages/Review/         # 自 loop/review 演化
  pages/Path/           # 新（吸收 onboarding reference/starter 交互）
  pages/Materials/      # 微调
  pages/Me/             # 瘦身
  features/content/
    chat/               # ChatThread, ChatInput
    confirm/            # ConfirmCard
    panes/              # DraftPane, PublishPack, VideoPack, BetPane
    project/            # ProjectStage, PathContextBar
    list/               # ProjectListRow 等
  features/path/        # PathProfile, BenchmarkReader, FormulaNote
  features/retro/       # RetroList
  services/api/v2/      # 增客户端
```

### 4.2 状态

- Zustand：`todayQueue`、`projectDraft`（本地恢复沿用 `projectDraft.ts`）、`chatScroll`  
- 路由：`/content/:projectId` 挂 `ProjectStage`（替换现 ContentPage 双分支）

### 4.3 组件迁移

| 现有 | 去向 |
|---|---|
| StageForms 各 Form | 拆为 ConfirmCard 字段 + 产物编辑；**删表单页流程** |
| ProjectWorkspace | 由 ProjectStage 取代（功能切片迁出） |
| ObservationList 等面板 | 入口关闭，数据只读进路径/公式 |
| ProjectListRow/StageMeter | 视觉保留、数据源改人话 nextActionLabel |

---

## 5. 编排与状态机

### 5.1 条级（ContentItem）

```
idea → angle_confirmed → drafting → ready_gate
     → bet_locked → published → retro_due → retro_done → settled
     ↘ video: shots → assembling → ready_gate
```

- 与 `ProjectStatus` 映射表兼容（additive 视图字段）  
- `ConfirmCard` 驱动跃迁；失败可重试；**无死路**

### 5.2 待决队列（Today）

查询：pending confirm_cards + retro_due + path_reminders + prepared_drafts（预产）。

---

## 6. 测试策略

| 层 | 要求 |
|---|---|
| 后端 | 先写红：skills 单测、API 契约、HumanGate 映射、人话化保真、bet 不可变、对标证据校验；覆盖率 ≥80% |
| 前端 | vitest：ConfirmCard、ProjectStage 四态、queue 过滤；覆盖率门禁不降 |
| E2E | **一条黄金路径**：快速开始→成稿→确认→登记→对账；对标导入冒烟；390 溢出 |
| 回归 | 旧 E2E 按映射改写，禁止成批删断言 |
| 契约 | OpenAPI 与文档 `contracts` 增补 |

### 质量命令（仓库既有）

```powershell
# backend
cd backend; python -m pytest
# frontend
cd frontend; pnpm lint; pnpm test; pnpm build; pnpm test:e2e
```

---

## 7. 迁移与兼容

| 步骤 | 内容 |
|---|---|
| 1 | 059–063 迁移（纯加） |
| 2 | 旧路由重定向（急稿/产出架/参考锚） |
| 3 | HumanGate API 保留；UI 改挂 ConfirmCard |
| 4 | 导出含新表；删除账号覆盖 path/formula/bet |
| 5 | 不删历史表；面板仅藏入口 |

---

## 8. 分阶段实现对齐业务

| 阶段 | 后端 | 前端 |
|---|---|---|
| P0 | 无/极少；清假状态 | 导航收敛、黄金 E2E |
| P1 | ConfirmCard、skills 雏形、queue API | ProjectStage 对话+产物、今日队列 |
| P2 | humanize、gate 一键修、bet、retro | 人话化无感、复盘页 |
| P2.5 | material gap/match、video package | VideoPack |
| P3 | PathProfile、BenchmarkRead、FormulaNote、exploration | 路径页 |
| P4 | learning_signals、回放、capability_trust | 进化可见区 |
| P5 | 发布适配、harness | 发布中心等 |

---

## 9. 风险

| 风险 | 缓解 |
|---|---|
| ContentPage 1200 行难拆 | 按 P1 切片替换路由，旧代码先分支后删 |
| 测试 36KB 断言 | 先基线清单再改 |
| ffmpeg 环境差异 | 无 ffmpeg 降级为剪辑清单 |
| 人话化伤事实 | 三档边界 + 单测对照样例 |
| 会话与产物不同步 | 单一 draft 状态源 + expected_version |
| 范围膨胀 | 严格按 P 阶段；P5 后置 |

---

## 10. 请确认

技术实现方案如上。回复：

- **「可以」** → 进入**任务拆解**（可执行 tasks.md / 实施顺序）  
- 或指出：表设计、API 路径、skills 划分、测试门禁、阶段切分等要改处
