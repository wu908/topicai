# TopicAI v4.0 静态分析报告

> 审查日期：2026-05-26
> 工具：ruff 0.15.14 / mypy 2.1.0 / pytest
> 范围：backend/ (84 个 .py 文件)

---

## 总览

| 工具 | 结果 |
|------|------|
| pytest | 206 passed / 0 failed |
| ruff | 50+ issues (F401, B904, I001, UP045 等) |
| mypy | 32 errors in 15 files |
| bandit | 未安装 |

---

## 一、Pytest 测试

```
============================ 206 passed in 23.02s =============================
```

全部通过。

---

## 二、Ruff 检查

### F401 — 未使用的 import（6 处）

| # | 文件 | 行号 | 未使用的 import |
|---|------|------|----------------|
| 1 | `app/api/v1/auth.py` | 6 | `fastapi.Depends` |
| 2 | `app/api/v1/profiles.py` | 9 | `datetime.datetime` |
| 3 | `app/api/v1/profiles.py` | 9 | `datetime.timezone` |
| 4 | `app/core/llm.py` | 22 | `config.llm_config.FUNCTION_TIERS` |
| 5 | `app/core/llm.py` | 25 | `config.llm_config.get_function_tier` |
| 6 | `app/core/exceptions.py` | 288 | `traceback` |

### B904 — except 子句缺少 from err（6 处）

| # | 文件 | 行号 | 说明 |
|---|------|------|------|
| 1 | `app/api/v1/auth.py` | 100 | `raise HTTPException(...)` 缺少 `from e` |
| 2 | `app/api/v1/auth.py` | 138 | 同上 |
| 3 | `app/api/v1/auth.py` | 168 | 同上 |
| 4 | `app/api/v1/ideas.py` | 25 | 同上 |
| 5 | `app/api/v1/profiles.py` | 55 | 同上 |
| 6 | `app/api/v1/profiles.py` | 64 | 同上 |

### I001 — import 块未排序（15+ 文件）

影响文件：`auth.py`, `feedback.py`, `ideas.py`, `profiles.py`, `llm.py` 及多个 service/middleware 文件。

### UP045 — Optional[X] 应改为 X | None（20+ 处）

**影响文件**：
- `app/core/exceptions.py` — 10 处
- `app/core/llm.py` — 3 处
- `app/services/creator_profile.py` — 4 处
- `app/api/v1/auth.py` — 2 处
- `app/middleware/error_handler.py` — 1 处

项目要求 Python 3.10+（`pyproject.toml` 中 `requires-python = ">=3.10"`），应统一使用 `X | None` 语法。

### 其他 Ruff 问题

| 规则 | 数量 | 文件 | 说明 |
|------|------|------|------|
| UP017 | 2 | `health.py:29,61` | `timezone.utc` 应改为 `datetime.UTC` |
| UP035 | 1 | `llm.py:15` | `typing.Type` 已废弃，应使用 `type` |
| F821 | 1 | `exceptions.py:256` | `app: "FastAPI"` 字符串注解中 FastAPI 未 import |

---

## 三、Mypy 类型检查

### 错误分类

| 类别 | 数量 | 严重性 | 说明 |
|------|------|--------|------|
| `no-any-return` | 10 | MEDIUM | 函数声明返回具体类型，实际返回 Any |
| `assignment` | 7 | HIGH | 类型不兼容的赋值 |
| `union-attr` | 5 | HIGH | 在联合类型上访问不存在的属性 |
| `attr-defined` | 3 | HIGH | 类型上不存在该属性 |
| `name-defined` | 1 | MEDIUM | 名称未定义 |
| `arg-type` | 1 | MEDIUM | 参数类型不匹配 |
| `index` | 2 | HIGH | 类型不支持索引赋值 |

### assignment — 类型不兼容（7 处）

| # | 文件 | 行号 | 问题 |
|---|------|------|------|
| 1 | `app/core/database.py` | 249 | `AsyncEngine` 赋值给 `None` 类型变量 |
| 2 | `app/core/database.py` | 259 | `None` 没有 `begin` 属性 |
| 3 | `app/core/database.py` | 281 | `async_sessionmaker` 赋值给 `None` 类型变量 |
| 4 | `app/chains/viral_chain.py` | 29 | `profile: dict = None` 类型不兼容 |
| 5 | `app/chains/track_chain.py` | 12 | `trends: list = None` 类型不兼容 |
| 6 | `app/chains/idea_chain.py` | 14 | `profile: dict = None` 类型不兼容 |

### no-any-return — 返回 Any（10 处）

| # | 文件 | 行号 | 声明返回类型 |
|---|------|------|-------------|
| 1 | `app/services/viral_analysis.py` | 50 | `dict[str, Any]` |
| 2 | `app/services/effect_review.py` | 175 | `float` |
| 3 | `app/data_sources/preloaded_source.py` | 81 | `list[dict[str, Any]]` |
| 4 | `app/data_sources/tianapi_source.py` | 174 | `bool` |
| 5-6 | `app/core/database.py` | 412, 434 | `int` |
| 7-8 | `app/core/llm.py` | 126, 266 | `str`, `T` |
| 9-10 | `app/core/auth.py` | 48, 62, 153, 173 | `str`, `bool`, `dict`, `str` |

### union-attr — APScheduler 类型问题（5 处）

| # | 文件 | 行号 | 问题 |
|---|------|------|------|
| 1-5 | `app/tasks/scheduler.py` | 44, 55, 65, 76, 86 | `object | Any` 没有 `add_job`/`start` 属性 |

### 其他错误

| # | 文件 | 行号 | 类别 | 问题 |
|---|------|------|------|------|
| 1 | `app/core/exceptions.py` | 256 | name-defined | `FastAPI` 未定义 |
| 2 | `app/core/database.py` | 412, 434 | attr-defined | `Result[Any]` 无 `rowcount` 属性 |
| 3 | `app/api/v1/feedback.py` | 26 | arg-type | `Any | None` 传入 `str` 参数 |
| 4 | `app/data_sources/data_manager.py` | 234, 236 | index | `Collection[str]` 不支持索引赋值 |
| 5 | `app/core/chroma.py` | 59 | attr-defined | `object` 无 `get_or_create_collection` 属性 |
| 6 | `app/core/llm.py` | 265 | attr-defined | `type[T]` 无 `model_validate` 属性 |

---

## 四、与手工审查的交叉验证

| 手工审查发现 | 工具验证 |
|-------------|---------|
| SQL 全参数化，无注入 | 确认 |
| 无 eval/exec 使用 | 确认 |
| 无 pickle 不安全反序列化 | 确认 |
| JWT 库 python-jose 已停维 | 确认 (3.3.0) |
| 缺少类型注解 | mypy 报告 10 处 `no-any-return` |
| passlib 已停维 | 确认 (1.7.4) |
| database.py 多次建引擎 | mypy 发现类型声明错误 |
| chain 层为占位代码 | mypy 发现 implicit Optional 错误 |

---

## 五、快速修复

### 自动修复

```bash
cd backend
.venv/Scripts/python.exe -m ruff check --fix .
```

可自动修复约 20 个问题（F401, I001, UP045, UP017）。

### 需手动修复的关键项

1. **database.py** — `self._engine` 和 `self._session_factory` 类型声明改为 `T | None`
2. **scheduler.py** — `scheduler` 类型从 `object` 改为正确的 APScheduler 类型
3. **chain 文件** — `param: dict = None` 改为 `param: dict | None = None`
4. **exceptions.py** — 在 `TYPE_CHECKING` 块中 import FastAPI
5. **data_manager.py** — `Collection[str]` 不支持索引赋值，改用具体类型
