# TopicAI 代码审查报告 (Phase 5-8 + Backend seg 1-3)

> 审查日期: 2026-06-03
> 审查工具: `codex review` (deepseek-v4-pro)
> 审查基准: `2210067` (上次审查的 fix commit)
> 审查范围: phase-5 ~ phase-8 前端 + backend-seg1 ~ seg3 后端
> 文件数量: 约 30 个变更文件 / 4000+ 行
> 验证方式: **已逐条独立 Read 验证**

---

## 总览

| 等级 | 数量 | 结论 |
|------|------|------|
| **CRITICAL / P1** | **3** | **BLOCK** — 须修复后再合并/部署 |
| **HIGH / P1** | **1** (含 P1 子项) | 必修 |
| **MEDIUM / P2** | **1** | 应修 |
| LOW | 0 | — |
| **合计** | **4 (1 项独立发现的 P1 共计 5)** | **BLOCK** |

> 0 严重/0 高危 ✅ 的目标未达成。**有跨租户数据修改风险 + 1 个生产环境 URL 拼接 Bug**,均阻塞任何多用户或非本地部署。

---

## 一、CRITICAL / P1 (必须修复)

### 1. `patch()` 方法 URL 拼接错误 —— 部署即坏
- **文件**: `frontend/src/services/api/client.ts:155-167`
- **问题**: `patch()` 方法使用 `API_PREFIX + url` 构建请求 URL,而 `get/post/put/delete` 均使用 `` `${BASE_URL}${url}` ``(`BASE_URL = API_BASE_URL + API_PREFIX`)。
  本地开发时 `VITE_API_BASE_URL=""`,两种写法输出相同;但**在设置了 `VITE_API_BASE_URL` 的 staging/production 环境中,所有 PATCH 请求会丢失 origin,直接打到当前域名的相对路径**。
- **影响调用**:
  - `setPrimaryAccount` (accounts)
  - `changeMemberRole` (accounts)
  - `updateAssetTags` (assets)
- **修复**:
  ```ts
  // line 158
  fetch(`${BASE_URL}${url}`, { ... })
  ```
  并同步修复 line 161 的 `body: data ? ...` → `body: data !== undefined ? JSON.stringify(data) : undefined`(与 `post`/`put` 一致,避免 `0`/`""`/`false` 被误判为无 body)。

---

### 2. `get_asset_usage` 端点缺少所有权校验 —— 跨租户读
- **文件**: `backend/app/api/v1/assets.py:57-65` + `backend/app/services/asset_service.py:119-125`
- **问题**: `GET /assets/{asset_id}/usage` 端点虽然依赖了 `get_current_user`,但**未把 `user["id"]` 传给 service**,`AssetService.get_usage(asset_id)` 也只接受 `asset_id`,SQL 是 `SELECT * FROM asset_usages WHERE asset_id = :aid` —— 无 `owner_id` 过滤。
- **影响**: 任何已登录用户**猜测/枚举 UUID 即可读取他人的素材使用记录**(包含 `article_id` 关联)。
- **修复**:
  - `assets.py:64` 改为 `result = await svc.get_usage(user["id"], asset_id)`
  - `asset_service.py:119` 改为 `async def get_usage(self, owner_id: str, asset_id: str)`,SQL 增加 `AND EXISTS (SELECT 1 FROM assets WHERE id = :aid AND owner_id = :oid)`,或先调用 `self.get(owner_id, asset_id)` 触发 `WHERE id=:id AND owner_id=:oid` 的现有校验。

---

### 3. `set_tags` 在所有权校验前提交数据 —— 跨租户写
- **文件**: `backend/app/services/asset_service.py:98-107`
- **问题**:
  ```python
  async def set_tags(self, owner_id: str, asset_id: str, tag_ids: list[str]) -> Asset:
      s = await self.db.get_session()
      try:
          await s.execute(text("DELETE FROM asset_tag_links WHERE asset_id = :aid"), {"aid": asset_id})   # ← 写入
          for tid in tag_ids:
              await s.execute(text("INSERT OR IGNORE ..."), {"aid": asset_id, "tid": tid})                 # ← 写入
          await s.commit()                                                                                  # ← 提交
      finally:
          await s.close()
      return await self.get(owner_id, asset_id)   # ← 所有权校验发生在 commit 之后
  ```
  - DELETE 的 SQL 也**没有 `owner_id` 过滤**,仅 `WHERE asset_id = :aid`。
  - 即便最终 `self.get` 抛 `ValueError`,受害者的 tag 关联**已物理删除**。
- **影响**: 调用 `PATCH /assets/{victim_asset_id}/tags` 即可清空他人素材的标签。UUID 虽然难猜,但属于**代码一致性 / 防御性**的硬错误(同文件 `delete()` 的 SQL 用了 `WHERE id=:id AND owner_id=:oid`)。
- **修复**:
  1. **先校验**:方法开头调用 `await self.get(owner_id, asset_id)` 触发现有 `WHERE id=:id AND owner_id=:oid` 检查,不通过则 `ValueError`。
  2. **顺带收紧 tag_ids 校验**:增加 `SELECT id FROM asset_tags WHERE id IN (...) AND owner_id = :oid` 验证 tag 归属当前用户,过滤掉越权 tag_id。

---

## 二、MEDIUM / P2 (应修)

### 4. `get_usage` 返回的 `article_title` 是 `article_id` —— 数据错误
- **文件**: `backend/app/services/asset_service.py:125`
- **问题**:
  ```python
  return [{"asset_id": r.asset_id, "article_id": r.article_id, "article_title": r.article_id, "used_at": r.used_at} for r in rows]
  ```
  `article_title` 直接复用 `r.article_id`(UUID),前端会展示一串 UUID 而不是人类可读的标题。
- **影响**: 前端资产使用记录 UI 显示无意义内容,体验 bug。
- **修复**:
  - 选项 A:在 SQL 里 `JOIN` 一张 `articles` 表取 `title`(若 schema 存在该表)。
  - 选项 B:在 `asset_usages` 表上 denormalize 一个 `article_title` 列(写入时由调用方传入)。
  - 选项 C(临时):返回结构里把 `article_title` 字段**直接删掉**,让前端用 `article_id` 自行查 title 端点;这是诚实的占位符,优于展示错误数据。

  > 建议:同时确认 `asset_usages` 表当前是否存在 `article_title` 列(本次审查未读 schema 全文)。若无,先选 **C**,后续按业务需求决定 A/B。

---

## 三、未被 Codex 报出、本次独立发现的 P1

### 5. `patch()` 内 body 序列化判断方式不一致
- **文件**: `frontend/src/services/api/client.ts:161`
- **问题**: `body: data ? JSON.stringify(data) : undefined` —— 使用 truthy 判断,会把 `0`、`""`、`false` 等合法值**误判为"无 body"**。`post`/`put` 用的是 `data !== undefined ? ...`,更安全。
- **修复**: 改为 `body: data !== undefined ? JSON.stringify(data) : undefined`,与 `post`/`put` 对齐。

---

## 四、建议修复顺序(单次 commit 内)

按"先堵安全,再修数据"的原则,一个 `fix: address Codex review Phase 5-8 + Backend seg 1-3` commit 内完成 5 项:

1. **`asset_service.set_tags`** —— 改写为"先 `self.get` 校验 → 再 DELETE/INSERT"(顺带校验 tag 归属)。
2. **`asset_service.get_usage`** —— 加 `owner_id` 参数,SQL 串 `AND owner_id`。
3. **`api/v1/assets.py:get_asset_usage`** —— 传 `user["id"]`。
4. **`client.ts:patch`** —— URL 用 `${BASE_URL}${url}` + body 判断改 `!== undefined`。
5. **`asset_service.get_usage`** —— `article_title` 字段临时改为不返回(选项 C),前端用 `article_id` 自查。

测试:跑 `pytest backend/tests/ -q`(已 28 通过,改后不能回归)+ `npx tsc --noEmit`(前端类型)。
