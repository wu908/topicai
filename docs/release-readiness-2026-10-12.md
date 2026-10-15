# 上线/验收准备清单 · 2026-10-12

## 测试门禁

| 套件 | 结果 |
|---|---|
| 后端 pytest | **533 passed** |
| 前端 vitest | **315 passed**（47 files） |
| Playwright e2e | **6 passed**（starter / intent / async-loop） |
| 前端 `pnpm build` | 成功 |
| `tsc` | 通过 |

## 部署形态（已具备）

```powershell
# 1) 配置
Copy-Item .env.example .env
# 编辑 JWT_SECRET_KEY（必填）、LLM_*、可选 OMNI_*

# 2) 构建并启动
docker compose up -d --build

# 3) 验收
# 前端: http://localhost
# 后端: http://127.0.0.1:8000/api/v2/health
```

- 后端仅绑定 `127.0.0.1:8000`，由前端 nginx 代理 `/api`
- 数据卷：`topicai_data` / `topicai_logs`
- SPA：`index.html` no-cache；`/assets/` 长缓存

## 本轮功能范围（可点验收）

- 设置整页（产品/全局 AI/项目助手/记忆/隐私）+ 后端持久化
- 双 AI 名称/头像；全局 AI 悬浮球
- 今日待决 + 轻创建（只记/立项）
- 项目屏：对话（ask）+ 确认卡（HumanGate）+ 产物/bet
- 周复盘对账/跳过；路径公式收/不收

## 已知边界（验收时勿当缺陷）

- UI 尚未 100% 按 Lumen 原型重绘（功能已通）
- 后端未建 path_profiles 等新表（prefs 存在 consent JSON）
- 多平台发布、视频精剪、移动端未做
- 模型 Key 在服务端 .env，不在设置页暴露

## 回滚

`git revert` 对应前端/后端提交；设置为 additive，无破坏迁移。
