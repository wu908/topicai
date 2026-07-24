# Spec 010 — Intent Model Migration

**状态**：草稿  
**分支**：`feature/intent-model-migration`  
**前置**：Spec 009 Phase F 完成（main `2f062ff`）

---

## 1. 背景与动机

Phase 21 完成后，领域访谈（`grill-with-docs`）确认了当前实现与领域模型之间的四处明确差距：

| 差距 | 现状 | 应有状态 |
|------|------|---------|
| Publish Judgment 字段 | 强制 `audience_problem` + `reader_promise`（所有意图） | 共享骨架 + 意图专属必填声明；problem/answer 仅属 solve |
| 意图确认与锁定 | `IntentStatus` 只有 `candidate/confirmed/legacy_missing` | Working Intent Confirmation 和 Intent Lock 是两个独立事件 |
| 旧数据分类 | `LEGACY_MISSING` 无法区分"未分类"与"已确认但缺锁定" | `legacy/unclassified` 保持待定；Retrospective Intent Classification 由用户确认后才进入意图学习 |
| Creator Series 约束 | 强制相同意图和相同形式 | Series 由 ongoing audience promise 连接，允许不同意图和格式 |

本 Spec 描述最小兼容迁移路径，**不改变任何已锁定 Publish Judgment 的历史记录**。

---

## 2. 范围

### 本 Spec 包含（首个垂直切片）

1. **Publish Judgment 公共骨架** — 意图中立的共享字段集合
2. **意图专属必填声明** — `solve/share/record` 各自的附加必填字段
3. **Working Intent Confirmation 与 Intent Lock 分离** — 两个独立状态与事件
4. **旧数据保持 `legacy/unclassified`** — 不默认映射为 `solve`；Retrospective Intent Classification 流程

### 本 Spec 不包含

- Creator Series 意图/格式约束调整（独立 Spec）
- 自动准备信任条件调整（独立 Spec）
- 前端 UI 流程变更（随后端合约稳定后跟进）

---

## 3. 领域术语（来自 CONTEXT.md）

| 术语 | 定义 |
|------|------|
| **Working Intent Confirmation** | 用户允许 AI 在当前 Primary Content Intent 下继续准备内容。在 Intent Lock 之前可修正。 |
| **Intent Lock** | Content Intent 和 Publish Judgment 成为一次发布不可变历史基础的时刻。锁定前可修正，锁定后追加而非覆盖。 |
| **Publication Intent** | Intent Lock 时保存的 Content Intent，作为创作者发布前认知的记录。 |
| **Publish Judgment** | 创作者发布前的判断：预期受众变化、预期反应、依据和不确定性，按 Content Intent 表达。problem/answer 仅属 solve 意图。 |
| **Complete Publish Judgment** | 共享受众、反应、依据、不确定性和 Observation Window 与 Primary Content Intent 要求的字段共同确认。 |
| **Unclassified Historical Content** | 发布时未锁定 Publication Intent 的导入或遗留内容。AI 可提议 Retrospective Intent Classification，但在用户确认前不进入意图专属学习。 |
| **Retrospective Intent Classification** | 用户确认的发布后解释，用于范围化未来对比和学习，不改变 Publication Intent。 |

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

**问题**：`audience_problem`（"受众面临的问题"）和 `reader_promise`（"读者承诺/解答"）是 solve 意图的专属概念。强制所有意图填写导致：
- share 意图被迫虚构"问题"
- record 意图被迫虚构"承诺"
- 学习数据污染：不同意图的 Publish Judgment 混用同一字段语义

### 4.2 `IntentStatus`（当前）

```python
class IntentStatus(StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"      # ← 无法区分 Working Confirmation vs Lock
    LEGACY_MISSING = "legacy_missing"  # ← 无法区分"未分类"与"缺锁定"
```

**问题**：
- `confirmed` 同时代表 Working Intent Confirmation 和 Intent Lock，但这是两个不同的用户决策和时间点
- `legacy_missing` 不区分"从未有过意图"和"有意图但系统未锁定"，导致无法安全做 Retrospective Intent Classification

---

## 5. 目标合约

### 5.1 Publish Judgment 公共骨架

所有意图共享：

```python
# 共享骨架（所有意图必填）
audience_change: str          # 预期受众变化（Audience Change）
primary_response: str         # 主要受众反应信号（Primary Response）
basis_refs: list[str]         # 依据引用
uncertainties: list[str]      # 不确定性
observation_window_days: int  # Observation Window（天数，发布前选定）
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
    content_intent: ContentIntent              # 新增：锁定时记录意图

    # 共享骨架
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
        elif self.content_intent == ContentIntent.SHARE:
            if not self.viewpoint_anchor:
                raise ValueError("share intent requires viewpoint_anchor")
        elif self.content_intent == ContentIntent.RECORD:
            if not self.continuation_promise:
                raise ValueError("record intent requires continuation_promise")
        return self
```

### 5.4 IntentStatus 目标

```python
class IntentStatus(StrEnum):
    CANDIDATE = "candidate"                  # AI 候选，未经用户确认
    WORKING_CONFIRMED = "working_confirmed"  # Working Intent Confirmation 完成
    LOCKED = "locked"                        # Intent Lock 完成（发布前）
    LEGACY_UNCLASSIFIED = "legacy/unclassified"  # 历史内容，无锁定记录
    RETROSPECTIVE = "retrospective"          # 用户完成 Retrospective Intent Classification
```

### 5.5 意图状态转换规则

```
CANDIDATE
    → WORKING_CONFIRMED   : 用户确认 Working Intent Confirmation（可重复修正，重回 CANDIDATE）
    → LOCKED              : 用户完成 Intent Lock（发布前，不可覆盖）

WORKING_CONFIRMED
    → CANDIDATE           : 用户修正意图（LOCKED 前可修正）
    → LOCKED              : 用户完成 Intent Lock

LOCKED
    → （不可变）           : 锁定后任何修正追加为 amendment，Publication Intent 不变

LEGACY_UNCLASSIFIED
    → RETROSPECTIVE       : 用户确认 Retrospective Intent Classification

RETROSPECTIVE
    → （不可变）           : 分类后进入意图专属学习范围
```

---

## 6. 迁移策略

### 6.1 旧数据处理原则

- **不删除、不修改**任何已锁定的 Publish Judgment 历史记录
- `LEGACY_MISSING` → 数据库中保持原值，读取层映射为 `legacy/unclassified`
- 旧的 `audience_problem` / `reader_promise` 字段值**保留**，标记为 `legacy_fields`
- 不自动推断意图；不将旧数据默认归为 `solve`

### 6.2 迁移 SQL 策略（migration 034）

```sql
-- 1. 为 publish_hypothesis 表新增意图相关列（可空，兼容旧记录）
ALTER TABLE publish_hypothesis ADD COLUMN content_intent TEXT;
ALTER TABLE publish_hypothesis ADD COLUMN audience_change TEXT;
ALTER TABLE publish_hypothesis ADD COLUMN primary_response TEXT;
ALTER TABLE publish_hypothesis ADD COLUMN observation_window_days INTEGER;
ALTER TABLE publish_hypothesis ADD COLUMN viewpoint_anchor TEXT;
ALTER TABLE publish_hypothesis ADD COLUMN continuation_promise TEXT;

-- 2. intent_status 新值（content_projects 表）
-- 旧 confirmed（未锁定）→ working_confirmed
-- 旧 legacy_missing → legacy/unclassified
-- 新增 locked、retrospective 值
-- 注意：不 UPDATE 现有行，新列在代码层处理映射

-- 3. 为 content_projects 表新增 intent_locked_at 时间戳列
ALTER TABLE content_projects ADD COLUMN intent_locked_at TEXT;
-- intent_locked_at IS NOT NULL 等价于 LOCKED 状态
```

### 6.3 兼容性边界

| 场景 | 处理方式 |
|------|---------|
| 旧 `audience_problem` / `reader_promise` 非空 | 保留在列，服务层读取时标记为 `legacy_solve_fields` |
| `intent_status = 'confirmed'`（旧值） | 服务层视为 `working_confirmed`，除非 `intent_locked_at` 非空 |
| `intent_status = 'legacy_missing'`（旧值） | 服务层视为 `legacy/unclassified` |
| 新 lock 请求中旧字段非空 | 拒绝；要求客户端使用新合约 |

---

## 7. 实现顺序

```
1. 合约层（models）
   - 更新 PublishHypothesisLock：新增意图专属字段 + model_validator
   - 更新 IntentStatus：新增 WORKING_CONFIRMED / LOCKED / LEGACY_UNCLASSIFIED / RETROSPECTIVE
   - 新增 RetrospectiveIntentClassification 合约

2. 迁移（migration 034）
   - 按 6.2 节 SQL 策略执行
   - 不修改现有行数据

3. 服务层（services）
   - publish_hypothesis: lock 路径检查意图专属字段
   - intent_actions: CONFIRM_INTENT 写入 working_confirmed；新增 LOCK_INTENT action type
   - 旧值兼容映射：confirmed → working_confirmed，legacy_missing → legacy/unclassified

4. 后端测试
   - solve lock 必须提供 audience_problem + reader_promise
   - share lock 必须提供 viewpoint_anchor
   - record lock 必须提供 continuation_promise
   - 跨意图字段混用必须被 validator 拒绝
   - 旧数据读取不崩溃，不默认映射为 solve
   - legacy/unclassified 不参与意图专属学习
   - Retrospective Classification 完成后才进入学习范围

5. 前端（后端稳定后跟进，独立 PR）
   - Publish Judgment 表单按意图动态显示专属字段
   - Intent Lock 作为独立确认步骤，与 Working Confirmation 分开

6. 覆盖率验证
   - 目标：保持 ≥ 80%
```

---

## 8. 不变量（Invariants）

以下约束在整个迁移过程中必须成立：

1. 已锁定的 Publish Judgment 字段不可被覆盖（仅追加 amendment）
2. `legacy/unclassified` 记录不自动进入 solve 意图的学习管道
3. Retrospective Intent Classification 必须由用户显式确认，AI 只可提议
4. `audience_problem` / `reader_promise` 在非 solve 意图的新 lock 请求中被拒绝
5. Working Intent Confirmation 和 Intent Lock 是两次独立的用户操作，不可合并

---

## 9. 踩坑防护

- 不删除 `audience_problem` / `reader_promise` 列（旧数据依赖）
- 不将旧 `confirmed` 状态直接 UPDATE 为 `locked`（缺少 `intent_locked_at` 证据）
- 不在 migration SQL 里 UPDATE 现有行的意图值
- 不把 `LEGACY_MISSING` 解释为"已知是 solve 意图"

---

## 10. 完成门槛

- [ ] migration 034 可重复运行，不修改现有行
- [ ] solve/share/record 的 lock validator 全部通过
- [ ] 旧数据读取测试：confirm → working_confirmed，legacy_missing → legacy/unclassified
- [ ] 跨意图字段混用被拒绝
- [ ] Retrospective Classification 合约存在且测试覆盖
- [ ] 后端 CI 通过，覆盖率 ≥ 80%
- [ ] `git diff --check` 通过
