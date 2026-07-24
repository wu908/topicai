# Spec 010 — Intent Model Migration

**状态**：草稿 v2（审查后修订）
**分支**：`feature/intent-model-migration`  
**前置**：Spec 009 Phase F 完成（main `2f062ff`）

---

## 1. 背景与动机

Phase 21 完成后，领域访谈（`grill-with-docs`）确认了当前实现与领域模型之间的四处明确差距：

| 差距 | 现状 | 应有状态 |
|------|------|---------|
| Publish Judgment 字段 | 强制 `audience_problem` + `reader_promise`（所有意图） | 共享骨架 + 意图专属必填声明；problem/answer 仅属 solve |
| 意图确认与锁定 | `IntentStatus` 只有 `candidate/confirmed/legacy_missing` | Working Intent Confirmation 和 Intent Lock 是两个独立事件 |
| 旧数据分类 | `LEGACY_MISSING` 无法区分"未分类"与"已确认但缺锁定" | `legacy_unclassified` 保持待定；Retrospective Intent Classification 由用户确认后才进入意图学习 |
| Creator Series 约束 | 强制相同意图和相同形式 | Series 由 ongoing audience promise 连接，允许不同意图和格式 |

本 Spec 描述最小兼容迁移路径，**不改变任何已锁定 Publish Judgment 的历史记录**。

---

## 2. 范围

### 本 Spec 包含（首个垂直切片）

1. **Publish Judgment 公共骨架** — 意图中立的共享字段集合（含 supporting_responses）
2. **意图专属必填声明** — `solve/share/record` 各自的附加必填字段
3. **Working Intent Confirmation 与 Intent Lock 分离** — 两个独立状态与事件
4. **旧数据保持 `legacy_unclassified`** — 不默认映射为 `solve`；Retrospective Intent Classification 流程

### 本 Spec 不包含

- Creator Series 意图/格式约束调整（独立 Spec）
- 自动准备信任条件调整（独立 Spec）
- 前端 UI 流程变更（随后端合约稳定后跟进）
- ADR 0002 学习管道约束（Evidence 边界、Comparable Samples 三样本要求、长期学习条件）由后续 Spec 承接

---

## 3. 领域术语（来自 CONTEXT.md）

| 术语 | 定义 |
|------|------|
| **Working Intent Confirmation** | 用户允许 AI 在当前 Primary Content Intent 下继续准备内容。在 Intent Lock 之前可修正。 |
| **Intent Lock** | Content Intent 和 Publish Judgment 成为一次发布不可变历史基础的时刻。锁定前可修正，锁定后追加而非覆盖。Lock 时 Publish Judgment 必须已完整。 |
| **Publication Intent** | Intent Lock 时保存的 Content Intent，作为创作者发布前认知的记录。不可被 Retrospective Intent Classification 覆盖。 |
| **Publish Judgment** | 创作者发布前的判断：预期受众变化、预期反应、依据和不确定性，按 Content Intent 表达。problem/answer 仅属 solve 意图。 |
| **Complete Publish Judgment** | 共享受众、主要反应、至多两个附加反应、依据、不确定性和 Observation Window 与 Primary Content Intent 要求的字段共同确认。 |
| **Unclassified Historical Content** | 发布时未锁定 Publication Intent 的导入或遗留内容。AI 可提议 Retrospective Intent Classification，但在用户确认前不进入意图专属学习。 |
| **Retrospective Intent Classification** | 用户确认的发布后解释，用于范围化未来对比和学习，**不改变 Publication Intent，存储于独立的 `retrospective_intent` 字段**。 |

---

## 4. 当前合约与差距

### 4.1 `PublishHypothesisLock`（当前）

```python
class PublishHypothesisLock(BaseModel):
    content_version_id: str
    audience_problem: str       # ← 所有意图强制，违反领域模型
    reader_promise: str         # ← 所有意图强制，违反领域模型
    expected_behaviors: list[ExpectedBehavior]
    basis_refs: list[str]
    uncertainties: list[str]
    expected_project_version: int
    idempotency_key: str
```

**问题**：`audience_problem` 和 `reader_promise` 是 solve 意图的专属概念。强制所有意图填写导致：
- share / record 意图被迫虚构字段值
- 学习数据污染：不同意图混用同一字段语义
- Complete Publish Judgment 的 supporting_responses 维度完全缺失

### 4.2 `IntentStatus`（当前）

```python
class IntentStatus(StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"          # ← 无法区分 Working Confirmation vs Lock
    LEGACY_MISSING = "legacy_missing"  # ← 无法区分"未分类"与"缺锁定"
```

**问题**：
- `confirmed` 同时代表两个不同用户决策，无法区分
- `legacy_missing` 无法安全做 Retrospective Intent Classification
- migration 020 的 CHECK 约束硬编码了这三个值，新状态写入时会被数据库拒绝

### 4.3 migration 020 的现有约束（⚠ 必须在 migration 034 中重建）

```sql
-- backend/app/data/migrations/020_intent_driven_actions.sql
ALTER TABLE content_projects ADD COLUMN intent_status TEXT NOT NULL DEFAULT 'legacy_missing'
    CHECK (intent_status IN ('candidate','confirmed','legacy_missing'));
```

新的 status 值（`working_confirmed`、`locked`、`legacy_unclassified`、`retrospective`）写入时会被此 CHECK 约束拒绝。**migration 034 必须重建此约束**（SQLite 需要建新表 + COPY + DROP 旧表方式）。

### 4.4 `audience_change` 字段已存在于 `IntentConfirmation`

```python
# intent_actions.py — Working Intent Confirmation 时填写
class IntentConfirmation(StrictModel):
    content_intent: ContentIntent
    audience_change: str = Field(min_length=1, max_length=1000)
    ...
```

`PublishHypothesisLock` 的共享骨架也需要 `audience_change`。
**规则**：Lock 时的 `audience_change` 可以是 Working Confirmation 时值的修正版本（用户在 Lock 前可修正），服务层写入 Lock 时使用请求体中的值，不自动复制 Confirmation 时的值。

---

## 5. 目标合约

### 5.1 Publish Judgment 公共骨架（所有意图必填）

```python
audience_change: str           # 预期受众变化（Audience Change）
primary_response: ExpectedBehavior   # 主要受众反应信号（Primary Response）
supporting_responses: list[ExpectedBehavior]  # 至多2个附加反应信号（Supporting Response）
basis_refs: list[str]          # 依据引用
uncertainties: list[str]       # 不确定性
observation_window_days: int   # Observation Window（天数，发布前选定）
```

### 5.2 意图专属必填声明

```python
# solve 专属
audience_problem: str   # 受众面临的问题（仅 solve）
reader_promise: str     # 读者可获得的方法/答案（仅 solve）

# share 专属
viewpoint_anchor: str   # 创作者视角/经历锚点（仅 share）

# record 专属
continuation_promise: str  # 读者可跟进的过程/变化（仅 record）
```

### 5.3 完整 `PublishHypothesisLock` 目标模型

```python
class PublishHypothesisLock(StrictModel):
    content_version_id: str = Field(min_length=1)
    content_intent: ContentIntent              # 锁定时记录意图（新增）

    # 共享骨架（所有意图必填）
    audience_change: str = Field(min_length=1, max_length=1000)
    primary_response: ExpectedBehavior
    supporting_responses: list[ExpectedBehavior] = Field(default_factory=list, max_length=2)
    basis_refs: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    observation_window_days: int = Field(ge=1, le=365)

    # solve 专属（仅 content_intent == "solve" 时必填）
    audience_problem: str | None = Field(default=None, max_length=1000)
    reader_promise: str | None = Field(default=None, max_length=1000)

    # share 专属（仅 content_intent == "share" 时必填）
    viewpoint_anchor: str | None = Field(default=None, max_length=1000)

    # record 专属（仅 content_intent == "record" 时必填）
    continuation_promise: str | None = Field(default=None, max_length=1000)

    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def require_intent_specific_fields(self):
        if self.content_intent == ContentIntent.SOLVE:
            if not self.audience_problem or not self.reader_promise:
                raise ValueError("solve intent requires audience_problem and reader_promise")
            if self.viewpoint_anchor or self.continuation_promise:
                raise ValueError("solve intent cannot include share/record-specific fields")
        elif self.content_intent == ContentIntent.SHARE:
            if not self.viewpoint_anchor:
                raise ValueError("share intent requires viewpoint_anchor")
            if self.audience_problem or self.reader_promise or self.continuation_promise:
                raise ValueError("share intent cannot include solve/record-specific fields")
        elif self.content_intent == ContentIntent.RECORD:
            if not self.continuation_promise:
                raise ValueError("record intent requires continuation_promise")
            if self.audience_problem or self.reader_promise or self.viewpoint_anchor:
                raise ValueError("record intent cannot include solve/share-specific fields")
        return self
```

### 5.4 IntentStatus 目标

```python
class IntentStatus(StrEnum):
    CANDIDATE = "candidate"                   # AI 候选，未经用户确认
    WORKING_CONFIRMED = "working_confirmed"   # Working Intent Confirmation 完成
    LOCKED = "locked"                         # Intent Lock 完成（发布前，不可变）
    LEGACY_UNCLASSIFIED = "legacy_unclassified"  # 历史内容，无锁定记录
    RETROSPECTIVE = "retrospective"           # 用户完成 Retrospective Intent Classification
```

注意：`LEGACY_UNCLASSIFIED` 使用下划线（非斜杠），与现有枚举风格一致，避免 URL/路径歧义。

### 5.5 意图状态转换规则

```
CANDIDATE
    → WORKING_CONFIRMED   : 用户确认 Working Intent Confirmation

WORKING_CONFIRMED
    → CANDIDATE           : 用户修正意图（LOCKED 前可修正，重置后可再次确认）
    → LOCKED              : 用户完成 Intent Lock
                            前置条件（guard）：Complete Publish Judgment 已填写完整
                            （即 model_validator 通过 + observation_window_days 已设定）

LOCKED
    → （不可变）           : 锁定后任何修正追加为 amendment，Publication Intent 不变

LEGACY_UNCLASSIFIED
    → RETROSPECTIVE       : 用户确认 Retrospective Intent Classification
                            （写入 retrospective_intent 字段，原 content_intent 保持 NULL）

RETROSPECTIVE
    → （不可变）           : 分类后进入意图专属学习范围（但 Publication Intent 仍为 NULL）
```

### 5.6 Retrospective Intent Classification 合约

```python
class RetrospectiveIntentClassification(StrictModel):
    """用户对历史内容的意图回顾性分类。
    
    不修改 content_intent（保持 NULL），
    写入独立的 retrospective_intent 字段。
    """
    retrospective_intent: ContentIntent      # 用户确认的回顾意图
    classification_basis: str = Field(min_length=1, max_length=2000)  # 分类依据
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
```

数据库对应：`content_projects` 表新增 `retrospective_intent TEXT` 列（可空）。

---

## 6. 迁移策略

### 6.1 旧数据处理原则

- **不删除、不修改**任何已锁定的 Publish Judgment 历史记录
- `intent_status = 'legacy_missing'`（数据库中保持原值），服务层读取时映射为 `legacy_unclassified`
- 旧的 `audience_problem` / `reader_promise` 字段值**保留**（已存在的列不删除）
- 不自动推断意图；不将旧数据默认归为 `solve`
- `retrospective_intent` 初始为 NULL，仅在用户显式确认后写入

### 6.2 迁移 SQL 策略（migration 034）

```sql
-- ============================================================
-- Step 1: 重建 content_projects.intent_status CHECK 约束
-- SQLite 不支持 ALTER CONSTRAINT，需要 CREATE + COPY + DROP
-- ============================================================

CREATE TABLE content_projects_new AS SELECT * FROM content_projects;

DROP TABLE content_projects;

CREATE TABLE content_projects (
    -- （从 000_initial_schema.sql + 各 ALTER 列完整重建）
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    -- ... 其余现有列 ...
    intent_status TEXT NOT NULL DEFAULT 'legacy_missing'
        CHECK (intent_status IN (
            'candidate',
            'confirmed',          -- 保留旧值，服务层做兼容映射
            'legacy_missing',     -- 保留旧值，服务层做兼容映射
            'working_confirmed',
            'locked',
            'legacy_unclassified',
            'retrospective'
        )),
    intent_locked_at TEXT,        -- 新增：Intent Lock 时间戳
    retrospective_intent TEXT     -- 新增：回顾性分类结果
        CHECK (retrospective_intent IN ('solve','share','record') OR retrospective_intent IS NULL)
);

INSERT INTO content_projects SELECT * FROM content_projects_new;
DROP TABLE content_projects_new;

-- ============================================================
-- Step 2: publish_hypothesis 表新增意图相关列（可空，兼容旧记录）
-- ============================================================

ALTER TABLE publish_hypothesis ADD COLUMN content_intent TEXT;
ALTER TABLE publish_hypothesis ADD COLUMN audience_change TEXT;
ALTER TABLE publish_hypothesis ADD COLUMN primary_response TEXT;
ALTER TABLE publish_hypothesis ADD COLUMN supporting_responses TEXT;  -- JSON 数组
ALTER TABLE publish_hypothesis ADD COLUMN observation_window_days INTEGER;
ALTER TABLE publish_hypothesis ADD COLUMN viewpoint_anchor TEXT;
ALTER TABLE publish_hypothesis ADD COLUMN continuation_promise TEXT;
```

> **注意**：Step 1 的 `CREATE TABLE content_projects` 语句必须包含 migration 020 之后所有 ALTER TABLE 累积的列。实现前需要从 `000_initial_schema.sql` + `020_intent_driven_actions.sql` 等整理完整列清单。

### 6.3 兼容性边界

| 场景 | 处理方式 |
|------|---------|
| `intent_status = 'confirmed'`（旧值） | 服务层视为 `working_confirmed`，除非 `intent_locked_at IS NOT NULL`（视为 `locked`） |
| `intent_status = 'legacy_missing'`（旧值） | 服务层视为 `legacy_unclassified` |
| 旧 `audience_problem` / `reader_promise` 非空 | 保留原列，新 lock 请求中由 model_validator 限制为 solve 专属 |
| 新 lock 请求（非 solve）携带 `audience_problem` | model_validator 拒绝 422 |
| `retrospective_intent` 非空但 `intent_status != 'retrospective'` | 数据异常，服务层记录 warning，不写入 |

---

## 7. 实现顺序

```
1. 合约层（models/v2/intent_actions.py + models/v2/publish_hypothesis.py）
   - 更新 IntentStatus：新增 WORKING_CONFIRMED / LOCKED / LEGACY_UNCLASSIFIED / RETROSPECTIVE
   - 更新 PublishHypothesisLock：新增共享骨架 + 意图专属字段 + model_validator（含跨字段排斥校验）
   - 新增 RetrospectiveIntentClassification 合约

2. migration 034
   - 重建 content_projects（扩展 CHECK 约束，新增 intent_locked_at + retrospective_intent）
   - 为 publish_hypothesis 追加意图相关列
   - 验证迁移可重复运行（幂等）

3. 服务层（以下文件全部需要更新 intent_status 判断逻辑）
   - backend/app/services/intent_actions.py     — CONFIRM_INTENT 写 working_confirmed；新增 LOCK_INTENT
   - backend/app/services/content_opportunity.py — confirmed 判断改为 working_confirmed OR locked
   - backend/app/services/intent_orchestrator.py — confirmed 判断同上
   - backend/app/services/creator_series.py      — confirmed 判断同上
   - backend/app/services/creator_viewpoint.py   — confirmed 判断同上
   - backend/app/services/blind_review.py        — legacy_missing 判断改为 legacy_unclassified
   - backend/app/services/content_genome.py      — intent_confirmed 逻辑更新（working_confirmed + locked 均算确认）
   - backend/app/services/publish_hypothesis.py  — lock 路径检查 intent_specific fields，写入 intent_locked_at

4. 后端测试（TDD：先写测试，再改服务层）
   - solve lock 必须提供 audience_problem + reader_promise，禁止其他意图专属字段
   - share lock 必须提供 viewpoint_anchor
   - record lock 必须提供 continuation_promise
   - 跨意图字段混用必须被 validator 拒绝（422）
   - WORKING_CONFIRMED → LOCKED 前置条件：Publish Judgment 不完整时拒绝
   - 旧 confirmed 行读取不崩溃，映射为 working_confirmed 或 locked
   - 旧 legacy_missing 行读取不崩溃，映射为 legacy_unclassified
   - legacy_unclassified 不参与意图专属学习
   - Retrospective Classification 写入 retrospective_intent，不修改 content_intent
   - retrospective 后进入学习范围，content_intent 保持 NULL

5. 前端（后端稳定后跟进，独立 PR）
   - Publish Judgment 表单按意图动态显示专属字段
   - Intent Lock 作为独立确认步骤，与 Working Confirmation 分开
   - supporting_responses 多选 UI（最多 2 项）

6. 覆盖率验证
   - 目标：保持 ≥ 80%
   - git diff --check 通过
```

---

## 8. 不变量（Invariants）

以下约束在整个迁移过程中必须成立：

1. 已锁定的 Publish Judgment 字段不可被覆盖（仅追加 amendment）
2. `legacy_unclassified` 记录不自动进入任何意图的学习管道
3. Retrospective Intent Classification 必须由用户显式确认，AI 只可提议
4. 非 solve 意图的新 lock 请求中，`audience_problem` / `reader_promise` 被 validator 拒绝
5. Working Intent Confirmation 和 Intent Lock 是两次独立的用户操作，不可合并
6. Retrospective Classification 写入独立的 `retrospective_intent` 字段；`content_intent` 对历史内容保持 NULL，不被回顾性分类覆盖
7. Intent Lock 只能在 Complete Publish Judgment 填写完整后执行（守卫条件）

---

## 9. 踩坑防护

- **不删除** `audience_problem` / `reader_promise` 列（旧数据依赖）
- **不将**旧 `confirmed` 状态直接 UPDATE 为 `locked`（缺少 `intent_locked_at` 证据）
- **不在** migration SQL 里 UPDATE 现有行的意图值
- **不把** `LEGACY_MISSING` 解释为"已知是 solve 意图"
- **不使用斜杠**作为 StrEnum 值（`legacy_unclassified` 而非 `legacy/unclassified`）
- migration 034 重建 `content_projects` 前，**必须列出所有累积列**，避免丢失 migration 020-033 的 ALTER 结果
- 更新服务层时，**8 处** `intent_status` 判断全部需要更新（见 §7 Step 3 清单）

---

## 10. 完成门槛

- [ ] migration 034 可重复运行，不修改现有行，CHECK 约束覆盖所有新旧状态值
- [ ] solve/share/record 的 lock validator 全部通过，跨意图字段混用被拒绝
- [ ] 旧数据读取测试：`confirmed` → `working_confirmed`，`legacy_missing` → `legacy_unclassified`
- [ ] `WORKING_CONFIRMED → LOCKED` 的 guard condition 测试（不完整 Judgment 被拒绝）
- [ ] Retrospective Classification：`retrospective_intent` 写入，`content_intent` 保持 NULL
- [ ] `legacy_unclassified` 不参与意图专属学习管道
- [ ] 后端 CI 通过，覆盖率 ≥ 80%
- [ ] `git diff --check` 通过
