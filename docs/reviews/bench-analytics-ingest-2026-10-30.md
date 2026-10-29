# 容量基准 · pilot5 analytics（2026-10-30）

> 目的：给 OG0 一个可复核的容量/延迟证据。**限制：in-memory SQLite、view 事件（无 project 归属查询）、单进程、非生产文件库**——只够支撑「默认关闭构建」的结论，不足以支撑启用签字（A9-03）。

## 1. 环境

- Python 3.13.5 / SQLite（aiosqlite）/ `AnalyticsService` 直调（不经 HTTP）。
- worktree `pilot5-first-party-analytics`，代码 `ed6ffb0`。
- 每批 32 条 `content_list_view`，跑 120 批；记录每批耗时。

## 2. 脚本（appendix，可复现）

```python
import asyncio, statistics, time, uuid, sys, datetime
sys.path.insert(0, r"G:\codex_project\topicAI\pilot5-first-party-analytics\backend")
from app.core.database import Database
from app.models.v2.analytics import AnalyticsEventIn
from app.services.analytics import AnalyticsService
from sqlalchemy import text

async def main():
    db = Database("sqlite+aiosqlite:///:memory:"); await db.init_db()
    s = await db.get_session()
    async with s:
        await s.execute(text("INSERT OR IGNORE INTO users (id,email,username,password_hash,ai_calls_today,ai_calls_reset_at,created_at) VALUES ('u1','u1@test.com','U1','h',0,'','2026-10-30T00:00:00Z')"))
        await s.commit()
    svc = AnalyticsService(db)
    ts = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00","Z")
    times=[]
    for _ in range(120):
        evs=[AnalyticsEventIn(event="content_list_view", payload={"group":"wanted","count":3}, client_ts=ts, idem_key=str(uuid.uuid4())) for _ in range(32)]
        t0=time.perf_counter(); await svc.ingest("u1", evs); times.append((time.perf_counter()-t0)*1000)
    times.sort()
    print("n=%d p50=%.2fms p95=%.2fms max=%.2fms" % (len(times), statistics.median(times), times[int(len(times)*0.95)-1], times[-1]))
    await db.close()

asyncio.run(main())
```

## 3. 输出（2026-10-30）

```text
first accepted 32 rejected 0
n=120 p50=24.00ms p95=25.58ms max=26.54ms
```

## 4. 容量估算

- 假设 <1,000 事件/天 → 90 天 <90,000 行；单行 <300 B（payload 小）→ <30 MB，含索引 <60 MB。
- 32 条/批 p95 25.6ms（内存库）→ 单进程足以吸收内测量级。

## 5. 不能证明什么

- 生产文件型 SQLite 的写放大/IO、并发请求、WAL 检查点开销；
- 真实 HTTP 栈（FastAPI/中间件）与鉴权成本；
- 事件突发（>1k/天）与 90 天清理缺失下的增长。

> 结论：默认关闭构建可发布；**启用前需按 OG0-r2 要求做生产近似压测与 A9-03 签字**。
