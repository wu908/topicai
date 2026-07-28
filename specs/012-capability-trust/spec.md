# Spec 012 — 自动置信条件调整（Per-Capability Auto-Prepare Trust）

**状态**：草稿 v1  
**分支**：`feature/capability-trust`  
**前置**：Spec 011 完成（`feature/creator-series-scope` 已合并或同基）

---

## 1. 背景与动机

ADR 0002 明确规定：

> Automatic preparation is authorized per capability after three accepted results,  
> never by a global trust score, and never includes protected decisions.

当前 `creator_state.py:refresh_trust()` 违反了这条约束：

| 位置 | 现状 | 与 ADR 0002 的冲突 |
|------|------|------------------|
| `creator_state.py:70` | `rate = accepted / total` | 这正是 ADR 0002 禁止的"全局信任分数（global trust score）" |
| `creator_state.py:72-75` | `eligible = completed_count >= 3 AND rate >= 0.8 AND …` | 用全局率（80% 接受率）代替逐 capability 三次计数 |
| `creator_state.py:72` | `completed_project_count >= 3` | 完成的项目数不等于某 capability 的已接受结果数 |

**后果**：用户完成三个不同 capability 的项目后，可能触发全局 `eligible`，但某个 capability（例如 `confirm_learning`）实际上从未被用户确认过，违反了"per capability"的独立授权原则。

---

## 2. 范围

### 本 Spec 包含

1. **新增 `capability_trust_json` 列**（migration 037）——按 `action_type` 存储已接受次数
2. **`refresh_trust()` 重写**——改为逐 capability 计数，移除全局比率作为资格判断条件
3. **`autopilot_eligible` 语义调整**——仅当所有受保护以外的 auto-prepare capability 均 ≥ 3 次已接受时为 `True`
4. **`CreatorState` 模型新增 `capability_trust` 字段**——暴露给 API 消费方
5. **测试**——TDD 验证 ADR 0002 三条约束

### 本 Spec 不包含

- `candidate_acceptance_rate` 列的删除（保留，供历史查询；不再影响 `eligible`）
- Comparable Samples 三样本要求（ADR 0002 §2，另行实现）
- Retrospective Intent Classification 前端 UI
- 观测窗口到期提醒

---

## 3. 设计决策

### §3.1 受保护决策（Protected Decisions）

以下 `action_type` 由用户主导，永远不进入自动准备路径，不参与信任计数：

| action_type | 原因 |
|-------------|------|
| `confirm_intent` | 用户确认自己的意图 |
| `lock_intent` | 用户锁定发布意图 |
| `create_project` | 用户发起新项目 |
| `answer_key_question` | 用户提供第一手信息 |
| `record_publication` | 用户记录发布 |
| `add_performance` | 用户填写表现数据 |
| `manage_learning` | 用户管理观测记录 |
| `confirm_publish_scope` | 用户确认发布范围 |

### §3.2 Auto-Prepare Capabilities

| action_type | 说明 |
|-------------|------|
| `review_candidate` | AI 准备候选内容草稿，等待用户审阅确认 |
| `confirm_learning` | AI 准备复盘摘要，等待用户确认学习结论 |

### §3.3 资格判断公式（新）

```
eligible =
    ∀ cap ∈ AUTO_PREPARE_CAPABILITIES:
        gate_confirmed_count(cap) ≥ 3
    AND unresolved_correction_count == 0
```

`candidate_acceptance_rate`（全局比率）不再参与资格判断；列保留供展示。

### §3.4 `capability_trust_json` 格式

```json
{
  "review_candidate": 4,
  "confirm_learning": 1
}
```

仅包含有实际事件的 capability，`get(cap, 0)` 处理缺省为 0。

---

## 4. 测试用例（TDD）

| # | 场景 | 期望 |
|---|------|------|
| T1 | 无任何事件 | `eligible=False`, `capability_trust={}` |
| T2 | `review_candidate` = 3, `confirm_learning` = 2 | `eligible=False`（confirm_learning 不足） |
| T3 | `review_candidate` = 3, `confirm_learning` = 3 | `eligible=True` |
| T4 | `review_candidate` = 10, `confirm_learning` = 0 | `eligible=False`（全局接受率 100% 不足为凭） |
| T5 | `review_candidate` = 3, `confirm_learning` = 3, `unresolved_correction_count` = 1 | `eligible=False`（有未解决修正） |
| T6 | `confirm_intent` = 100（受保护） | 不计入 capability_trust，不影响 eligible |
| T7 | `capability_trust_json` 持久化 | refresh_trust() 后 DB 列已更新 |

---

## 5. 迁移说明

Migration 037 (`037_capability_trust.sql`)：

```sql
ALTER TABLE creator_states
    ADD COLUMN capability_trust_json TEXT NOT NULL DEFAULT '{}';
```

无需 post-step（ADD COLUMN + DEFAULT 在 SQLite 中原生支持，无需表重建）。

---

## 6. 完成门槛

| 门控 | 验收标准 |
|------|---------|
| T1–T7 全部通过 | `pytest tests/services/test_creator_state.py` 7/7 |
| 全局信任率不再影响 eligible | `rate=1.0, count<3` → `eligible=False` |
| per-capability 计数 ≥ 3 时 eligible | T3 通过 |
| `capability_trust` 出现在 API 响应 | `CreatorState` model 字段存在 |
| 后端覆盖率 ≥ 80% | `pytest --cov=app --cov-fail-under=80` |
| `git diff --check` | 无空白错误 |
