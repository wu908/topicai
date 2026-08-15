# ADR-003: 历史 SQL 迁移 critical 风险记录与处置策略

> 状态：已接受（accepted）
> 日期：2026-08-10
> 来源：全库审计 `be776634` 的 15 条 critical 发现

## 背景

全库静态扫描（ocr 会话 `be776634`）在已落库的历史 SQL 迁移文件中发现 15 条
critical 级问题。这些问题集中在 `backend/app/data/migrations/031`–`045` 范围内。

## 核心约束

- 迁移 runner（`runner.py`）记录每个迁移的 SHA-256 校验和，修改历史文件会让新旧库分叉
- 已执行的迁移无法回滚，数据可能已在历史迁移中被转换
- SQLite 的 `PRAGMA foreign_keys=OFF` 在显式事务内是 no-op（SQLite 文档明确说明）

## 问题分类

### 已修复（1/15）

| 迁移 | 问题 | 修复方 |
|---|---|---|
| 033 | 触发器无锁态守卫，draft 行也被拦截 | `049_release_audit_batch3.sql` |

### 模式 A：INSERT OR IGNORE + DROP TABLE 静默丢数据（045）

`045_drop_legacy_v1_tables.sql` 先 `INSERT OR IGNORE INTO materials ... SELECT FROM assets`，
然后 `DROP TABLE assets`。不符合新 schema 的行被静默跳过后原表销毁，数据永久丢失。

**风险等级**：仅影响 v1→v2 一次性迁移，新库无此路径；既有库已执行完毕。

### 模式 B：表重建时 PRAGMA foreign_keys=OFF 在事务内无效（031/032/043）

这三个迁移都在 `executescript()` 内执行 `PRAGMA foreign_keys=OFF` 后 DROP 旧表。
SQLite 文档：事务内的 PRAGMA 不会改变连接状态，因此 DROP 可能触发级联删除子表行。

- 031：`DROP TABLE human_gates_before_privacy`
- 032：`DROP TABLE content_opportunities_before_source_verification`
- 043：`DROP TABLE content_opportunity_events_before_first_party`

**风险等级**：`_before_*` 临时表无子表 FK 引用（它们是 RENAME 后的旧表），
实际级联风险低；但 043 的 RENAME 操作中途失败会导致下次启动卡死。

### 模式 C：post-step 幂等性与控制流不一致（036）

`036_creator_series_scope.sql` 只有注释，逻辑在 runner.py 的 post-step。
已执行过 post-step 的数据库不会再次执行，注释描述的"dropping NOT NULL"
与 runner 实际行为存在措辞不一致。

**风险等级**：纯文档/控制流一致性问题，无数据风险。

## 决策

1. **不修改历史迁移文件** — 校验和已记录，修改会让既有库与新库分叉
2. **049 已修复触发器问题** — 033 的 critical 已关闭
3. **模式 A/B 的实际风险已过期** — 这些迁移在所有既有库上已执行完毕，
   临时表已 DROP，数据已转换。新增审计迁移只能做"事后检查"，无法修复已丢失的数据
4. **记录为 ADR** — 未来如有类似表重建迁移，应遵循 `048` 的原子重建模式
   （显式 BEGIN + DROP IF EXISTS + rollback on failure）

## 后续迁移的安全模式（供参考）

新的表重建迁移应遵循 `_post_step_048` 的模式：

```python
conn.execute("PRAGMA foreign_keys=OFF")  # 在事务外
try:
    conn.execute("BEGIN")                # 显式事务
    conn.execute("DROP TABLE IF EXISTS _new")  # 清理崩溃残留
    conn.execute(new_table_sql)
    conn.execute("INSERT INTO _new SELECT ... FROM old")
    conn.execute("DROP TABLE old")
    conn.execute("ALTER TABLE _new RENAME TO old")
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.execute("PRAGMA foreign_keys=ON")
```
