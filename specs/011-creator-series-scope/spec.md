# Spec 011 — Creator Series Scope Relaxation

**状态**：草稿 v1
**分支**：`feature/creator-series-scope`
**前置**：Spec 010 完成（main `4afe1e2`）

---

## 1. 背景与动机

Spec 010 §2 明确把 Creator Series 的意图/格式约束排除在外，留给独立 Spec。这是领域访谈确认的四处差距中最后一处未处理的。

CONTEXT.md 的领域定义：

> **Creator Series**: A user-confirmed relationship among published Content Projects that share an ongoing audience promise and continuation, while each project retains its own intent, format, Publish Judgment, and review lens.

当前实现与之矛盾：

| 位置 | 现状 | 与领域定义的冲突 |
|------|------|-----------------|
| `creator_series.py:60-63` | 源项目意图或格式不一致时 `ValueError` | Series 由 ongoing audience promise 连接，不由相同意图/格式连接 |
| `creator_series` 表 | `content_intent` / `content_format` 为 `NOT NULL` 标量列 | 假设整个 Series 只有一个意图和一种格式 |
| `creator_series.py:404-409` | 确认/使用时二次校验成员意图/格式等于 Series 标量值 | 同上 |
| `content_genome.py:390-396` | 用 Series 标量意图/格式做过滤，不匹配即跳过 | 混合意图 Series 没有唯一对照值 |
| `content_opportunity.py:261-262, 418` | 延展机会直接继承 Series 标量意图/格式 | Series 无单一意图后新项目意图无来源 |

**后果**：创作者不能把「同一个受众承诺下、意图或形式不同」的已发布内容确认为一个系列。例如一篇 solve（给方法）+ 一篇 record（记录方法失效后的调整）本属同一承诺，当前被 422 拒绝。

---

## 2. 范围

### 本 Spec 包含

1. **Series 成员意图/格式可不同** — 移除 propose 时的同意图同格式强制
2. **Series 意图/格式标量降级为非权威** — 保留列（旧数据依赖），仅在成员一致时有值，混合时为 NULL
3. **`scope_json` 记录成员集合** — `member_intents` / `member_formats`
4. **ContentGenome 成员任一意图匹配即命中**（决策 a）
5. **`series_extension` 机会的意图/格式由 AI 提议、用户接受时确认**（决策 a）

### 本 Spec 不包含

- 自动准备信任条件调整（独立 Spec）
- ADR 0002 学习管道约束（Evidence 边界、Comparable Samples 三样本要求）
- Retrospective Intent Classification 前端 UI
- 观测窗口到期提醒
- Series 成员的 Publish Judgment / review lens 变更（各项目已各自独立，无需改动）

---

## 3. 设计决策

### 3.1 混合意图 Series 在 ContentGenome 的过滤语义（决策 a）

**选定**：成员任一意图匹配则命中。

`content_genome.py` 的 series 过滤改为：查询意图存在时，若 `member_intents` 含该意图则保留，否则跳过；格式同理。

**理由**：Series 仍受意图约束地进入 genome，跨意图污染面最小，符合 Spec 010 留下的「意图专属学习管道」不变量。

**被否决的替代方案**：
- Series 彻底意图中立、永远命中 —— 最贴近 promise 的意图中立性，但 series_context 会流进任意意图的准备上下文，等于开一条新学习通路，需要独立的证据边界设计
- 保留派生「主意图」字段 —— 把刚要拆掉的单一意图假设留在数据里

### 3.2 `scope_json` 形状与 `_applicability` 兼容

`CreatorRuleService._applicability` 读 `scope["content_intent"]` 和 `scope["format"]`，缺失即视为该维度「宽」（不是通配）。`_match_status` 在 applicability 有值且与查询不等时返回 `not_applicable`。

因此 scope 写入规则：

```python
scope = {
    "member_intents": sorted(member_intents),   # 始终写入
    "member_formats": sorted(member_formats),   # 始终写入
}
if len(member_intents) == 1:
    scope["content_intent"] = single_intent     # 仅一致时写入
if len(member_formats) == 1:
    scope["format"] = single_format             # 仅一致时写入
```

- **成员一致**：scope 形状与今天完全相同 + 两个新键 → `_applicability` 行为不变，现有测试语义不变
- **成员混合**：两个标量键缺失 → applicability 在该维度为「宽」→ `_match_status` 不会因格式不匹配判 `not_applicable`，也不会加 `missing_format_context`

### 3.3 `series_extension` 机会的意图/格式来源（决策 a）

**选定**：AI 在 draft 中提议 `content_intent` / `content_format`，用户接受机会时确认。

- 新增合约 `SeriesExtensionDraft(OpportunityDraft)`，附加 `content_intent` / `content_format` 两个必填字段。不改 `OpportunityDraft` 本身，避免影响 `user_source` 路径。
- `OpportunityDecision` 新增可选 `confirmed_content_intent` / `confirmed_content_format`，用户接受时可覆盖 AI 提议；为 `None` 时沿用提议值。
- 模型不可用的确定性兜底：成员一致时用该意图/格式；混合时用**最近一篇成员项目**的意图/格式，并在 `limitations` 中声明「意图为兜底推断，需用户确认」。

**理由**：机会的定义本就是「可解释、用户可决策的候选」，意图作为提议的一部分最自然；不需要给 `SeriesExtensionCreate` 加必填字段，前端提出延展的调用不变。

**被否决的替代方案**：
- 用户提出延展时显式指定 —— 需改请求合约和前端调用
- 隐式继承最近一篇成员项目的意图 —— 用户没做过这个决策，违背 Spec 010「AI 只可提议」的基调

### 3.4 列保留策略

`creator_series.content_intent` / `content_format` **不删除**，改为可空。与 Spec 010 对 `audience_problem` / `reader_promise` 的处理一致：旧数据依赖这两列，删除会破坏历史记录。

语义降级为「成员一致时的便捷读取值」，混合时为 NULL。所有权威判断改读 `scope.member_intents` / `scope.member_formats`。

---

## 4. 目标合约

### 4.1 `SeriesExtensionDraft`（新增）

```python
class SeriesExtensionDraft(OpportunityDraft):
    content_intent: Literal["solve", "share", "record"]
    content_format: Literal["graphic_note", "vlog_plan"]
```

### 4.2 `OpportunityDecision`（追加两个可选字段）

```python
class OpportunityDecision(StrictModel):
    ...                                                    # 现有字段不变
    confirmed_content_intent: Literal["solve","share","record"] | None = None
    confirmed_content_format: Literal["graphic_note","vlog_plan"] | None = None
```

### 4.3 Series 读模型（`_normalize` 输出）

```
content_intent: str | None          # 成员一致时为该意图，混合时 None
content_format: str | None          # 同上
scope: {
    member_intents: list[str],      # 始终存在，去重排序
    member_formats: list[str],      # 始终存在，去重排序
    content_intent?: str,           # 仅成员一致时存在
    format?: str,                   # 仅成员一致时存在
}
```

### 4.4 ContentGenome series 节点与 series_context

追加 `member_intents` / `member_formats`；`content_intent` / `content_format` 保留但可为 `null`。

---

## 5. 数据迁移

### migration 036 — `creator_series` 列可空 + 回填 scope 成员集合

`creator_series.content_intent` / `content_format` 的 `NOT NULL` 与 CHECK 约束需要 SQLite 表重建（`ALTER CONSTRAINT` 不支持）。沿用 `_post_step_034_intent_model` 的 `foreign_keys=OFF` 重建模式。

**post-step `_post_step_036_creator_series_scope`**：

1. 幂等检查：表 SQL 中 `content_intent TEXT NOT NULL` 已不存在则直接返回
2. `PRAGMA foreign_keys=OFF` → 建新表（两列可空，CHECK 允许 NULL）→ 逐列 COPY → DROP 旧表 → RENAME → 重建索引
3. 回填：对每行 `scope_json` 补齐 `member_intents` / `member_formats`。已有行成员一致（旧约束保证），因此从现有标量值推导：`member_intents = [content_intent]`，`member_formats = [content_format]`
4. `PRAGMA foreign_keys=ON` + `PRAGMA foreign_key_check` 校验

**不做**：不 UPDATE 任何 `content_intent` / `content_format` 现有值为 NULL。旧 Series 成员一致，标量值仍然正确。

---

## 6. 服务层变更

| 文件 | 变更 |
|------|------|
| `creator_series.py:60-63` | 删除 `len(intents) != 1 or len(formats) != 1` 拒绝；改为计算成员集合 |
| `creator_series.py:69-71` | `intent` / `content_format` 仅在集合大小为 1 时取值，否则 `None`；`scope` 按 §3.2 构造 |
| `creator_series.py:397-409` | `_assert_sources_available` 改为比较当前成员集合与 scope 中记录的成员集合 |
| `creator_series.py:307-330` | `_attach_creator_state` 的 insight 追加 `member_intents`；`content_intent` 可为 None |
| `creator_series.py:332-370` | `_draft` prompt 已逐项列出各成员意图，无需改动；兜底 promise 措辞不变 |
| `content_genome.py:390-396` | 过滤改为成员任一匹配（旧行无 member 键时回退读标量） |
| `content_genome.py:420-430, 455-470` | node 与 series_context 追加 `member_intents` / `member_formats` |
| `content_opportunity.py:_draft` | 返回 `SeriesExtensionDraft`；兜底按 §3.3 推断意图/格式并加 limitation |
| `content_opportunity.py:248-262` | 插入使用 draft 的意图/格式，不再读 Series 标量 |
| `content_opportunity.py:418` | `MATERIALS_BY_INTENT[draft.content_intent]` |
| `content_opportunity.py:decide` | 接受时套用 `confirmed_content_intent` / `confirmed_content_format` 覆盖 |

---

## 7. 前端变更

| 文件 | 变更 |
|------|------|
| `types/contracts/v2/content.ts` | `CreatorSeries.content_intent` / `content_format` 改可空；genome series 节点与 context 追加 `member_intents` / `member_formats`；`OpportunityDecision` 追加两个可选字段 |
| Series 展示位置 | 意图为 NULL 时展示成员意图集合，不展示空值 |

---

## 8. 测试计划（TDD）

### 后端

1. `propose` 接受不同意图的已发布项目 → `content_intent is None`，`scope.member_intents == ["record","solve"]`
2. `propose` 接受不同格式 → `content_format is None`，`scope.member_formats` 含两项
3. 成员一致时 scope 仍含 `content_intent` / `format` 标量键，行为与旧实现一致（回归）
4. 混合意图 Series 在 genome 中：查询意图属于成员集合 → 命中；不属于 → 跳过
5. 混合格式 Series 不因 `format_scope_mismatch` 被判 `not_applicable`
6. `_assert_sources_available`：成员意图在 Series 确认后被改变 → `ValueError`
7. `series_extension` 提议：AI 返回意图/格式 → 写入机会行
8. `series_extension` 兜底（LLM 不可用）+ 混合 Series → 取最近成员意图，limitations 含需确认声明
9. `decide(accept)` 带 `confirmed_content_intent` → 创建的项目使用覆盖后的意图
10. `decide(accept)` 不带覆盖 → 使用提议意图
11. migration 036 幂等：连续运行两次不报错，checksum 记录一次
12. migration 036 回填：旧行 scope 补齐成员集合，标量值不变

### 前端

13. Series 卡片在 `content_intent` 为 null 时渲染成员意图集合

---

## 9. 不变量（下游须遵守）

- Series 的权威意图/格式信息是 `scope.member_intents` / `scope.member_formats`；标量列仅在成员一致时有值
- Series 成员各自保留自己的意图、格式、Publish Judgment 和 review lens，Series 不覆盖任何成员字段
- 混合意图 Series 只在查询意图属于成员集合时进入 genome（不是意图中立通配）
- `series_extension` 机会的意图/格式是 AI 提议值，必须经用户接受才写入项目
- `creator_series.content_intent` / `content_format` 列不可删除
- Series 确认后成员意图/格式集合发生变化 → 使用时拒绝（与现有 scope 漂移检测一致）

---

## 10. 完成门槛

| 门控 | 说明 |
|------|------|
| migration 036 幂等 | runner checksum 追踪，重复运行无副作用 |
| 混合意图/格式 Series 可提出并确认 | 不再抛 `share content intent and format` |
| 成员一致 Series 行为不变 | 现有 creator_series / genome 测试全绿 |
| genome 成员任一意图匹配 | 命中与跳过两个方向都有测试 |
| 延展机会意图由用户确认 | 覆盖与沿用两条路径都有测试 |
| 后端覆盖率 ≥ 80% | `pytest --cov=app --cov-fail-under=80` |
| `git diff --check` | 无空白错误 |
