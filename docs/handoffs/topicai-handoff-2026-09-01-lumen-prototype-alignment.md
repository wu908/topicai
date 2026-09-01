# TopicAI 交接：原型 → 实现 100% 对齐（Lumen 前端交付完成）

> 日期：2026-09-01
> 分支：`main` @ `643f3bc`（与 `origin/main` 完全同步，0 未推送）
> 演示服务当前在线：前端 http://127.0.0.1:5173 · 后端 8765（演示库 `data/e2e/`，AI 关闭）
> 上一份交接：`docs/handoffs/topicai-handoff-2026-08-31-spec013-phase1-dogfood.md`

---

## 1. 结论

**Lumen 前端开发全批次完成，原型（`docs/prototypes/hifi-lumen.html`）的每一屏 + 对话层现有一一对应的真实实现，全部推送且 CI 绿。** 本会话后半程新增的关键工作：**信息架构重排（此前“皮同骨不同”的根本修正）** 与**剩余五处结构对齐**。后端与前端功能对齐（既有 E2E 全链路验证）；与原型的分歧只剩计划内事项（见 §6）。

## 2. 本轮提交序列（旧 → 新）

| 提交 | 内容 |
|---|---|
| `c20afd6` | fix: 保留“你好，”标题前缀（E2E 契约） |
| `25000a2` | 批次 3：晨报信 + 玻璃操作容器 |
| `eaa00c3` | fix: 悬浮球装饰层 pointer-events（E2E 导航拦截） |
| `0ba1e96` | feat: 对话注入点接线（产出卡“问它”/周复盘点“问”）+ 晨报安静数据条 |
| `2353090` | **IA 重排**：侧栏双组（创作=晨报/产出架/收件箱/急稿/周复盘，管理=内容/机会/素材/我的）；/loop 精简为产出架；新页 /loop/inbox、/loop/review、/urgent（三步建项目，零新增后端） |
| `643f3bc` | **剩余对齐**：产出架双栏（卡流/粘性拾取面板）、登录原型化（中央玻璃卡）、成长页 /growth（解除门控：真实计数 + 诚实“待达成”态）、晨报 3 快捷意图、悬浮球主动缺口推送 |

早前批次（已推）：`7c32d49`（DESIGN.md v3 + Spec-013 骨架）、`44200fb`/`e7fd7ac`（后端骨架/前端 /loop）、`5c544ea`/`b821f6d`（周度复盘+E2E/CI 修复）、`eb5bd96`（PublishCheck）、`d5d65b0`（批次 1 令牌/主题/背景场）、`7130c90`+`3c5f906`（批次 2 悬浮球系统）。

## 3. 当前状态快照

- **前端**：原型 7 屏 + 对话层全部落地（见 §4 对照表）；侧栏 10 项双组；`DESIGN.md` v3 为唯一设计权威；MUI 令牌 + CSS 变量双轨（`tokens.css` `--v3-*` 值 = Lumen；`--color-*` 已改别名防漂移）；动效编排 GSAP 3.15（用 pnpm@10.34.5 装——本仓库 node_modules 由 pnpm10 构建，pnpm11 会拒绝写 store，bootstrap 纪律）。
- **后端**：未变（Spec-013 Phase 1 四表/四服务/路由 + 周度聚合 + PublishCheck），迁移至 051。
- **测试**：后端 410+ / 前端 **242 单测**（覆盖率 79.9-70.4-71.0-82.5，门槛 80/66/66/76）/ E2E 6 passing（导航断言覆盖全部 10 节点）。
- **CI**：每笔 push 绿；工作树干净。

## 4. 原型 ↔ 实现对照（交接后用）

| 原型屏 | 路由/组件 | 备注 |
|---|---|---|
| 登录（中央玻璃卡） | `/login`（LoginPage） | 已去右营销面板；E2E 依赖 `#login-email/#login-password` + 按钮“登录” exact |
| 晨报（信+数据+快捷意图+任务卡） | `/`（HomePage） | 标题断言 `/^你好，/`（E2E 契约勿破坏） |
| 产出架（双栏）+ 拾取 | `/loop`（AsyncLoopPage） | **双栏**=左卡流/右粘性面板；移动端卡内折叠；“事实清单/希望读者的变化/认领”在 DOM 出现两处（卡内+右栏），E2E 用 `.first()/.last()` |
| 收件箱 + 证伪线度量 | `/loop/inbox`（InboxPage） | |
| 急稿 · 三步 | `/urgent`（UrgentPage） | 创建项目→confirm intent→跳 `/content/:id`；无新后端 |
| 周复盘（判断 vs 实际） | `/loop/review`（ReviewPage） | 聚合只读；确认动作仍在项目工作台 HumanGate |
| 成长（资产/里程碑/信任） | `/growth`（GrowthPage） | 真实计数（creator state/观点/系列/项目）；里程碑“待达成”诚实态；**本轮按用户指令解除 Phase 4 门控。后续若要“能力信任写接口/等级化”，需新规格** |
| 悬浮球对话 | `features/companion/` | `openCompanion(ctx)` 注入契约；四幕 GSAP 首启；12s 渐隐；主动缺口推送（演示文案） |

## 5. 关键纪律（新会话继续遵守）

1. **pnpm 用 10.34.5**（`npx -y pnpm@10.34.5 …`），pnpm11 仅读不写。
2. **E2E 后端生命周期由 playwright 管理**（`frontend/playwright.config.ts`：托管 uvicorn、`e2e_reset.py` 预清理、AI 关、限流放宽、reuse=false）；本地单独截图需手动起后端（见 REPL 习惯：`data/e2e` 目录必须存在）。
3. **E2E 文本断言**：侧栏 10 节点、`/^你好，/`、双栏重复文案处理——改 UI 文案前先 grep `e2e/*.spec.ts`。
4. **模型凭据**：`backend/.env` 本地真实 key，绝不入 git；测试已免疫（conftest 强制重读 Settings 单例）。
5. **原型路径**：`docs/prototypes/hifi-lumen.html`（未 Git 追踪，工作文件）；截图在 `docs/prototypes/screenshots/lumen-app-*.png`（同样未追踪）。

## 6. 剩余事项（优先级序）

1. **移动端手检**：产出架双栏的 `<768px` 折叠（卡内拾取）未经实机/浏览器移动视口手检——E2E 仅覆盖导航溢出。
2. **生长页深化**（若继续）：接“能力信任”写接口（项目级 automation 偏好已有 API）与里程碑点亮逻辑——需新 Spec 批准（原 Phase 4 内容）。
3. **狗粮期**（Phase 2）：协议在 `docs/testing/dogfood-falsification-protocol.md`；等测试者招募；两条线不达标即回炉方向。
4. **清理**：`backend/data/e2e/` 演示库（gitignore 已含）；`/tmp/*.log` 本地临时。
5. **低优**：前端 branches 门禁 66→65% 目标未达成的其余 P2 审计项（`docs/reviews/test-suite-audit-2026-08-31.md`）。

## 7. 建议技能（Suggested skills）

- `design-taste-frontend` + `stitch-design-taste`：新界面/组件 Pass（判读拨盘 + Pre-Flight 清单）
- `gsap-timeline` / `gsap-core`：对话/动效编排后续
- `redesign-existing-projects`：UI 差异审计时用（审计-诊断-修复）
- `windows-wsl-docker-validation`：容器复验（本机 WSL 需管理员上下文）
- `handoff`：下次交接沿用（按用户指定落 `docs/handoffs/`）

## 8. 演示环境重启指令

```powershell
# 后端（演示库）
cd backend; mkdir -p data/e2e/objects
DATABASE_URL='sqlite+aiosqlite:///G:/codex_project/topicAI/mvp/backend/data/e2e/e2e.db' OBJECT_STORAGE_ROOT='G:/codex_project/topicAI/mvp/backend/data/e2e/objects' JWT_SECRET_KEY='e2e-secret-key-for-local-run-2026' AUTH_RATE_LIMIT_PER_MINUTE=100 AI_ENABLED=false .venv\Scripts\python.exe -m uvicorn main:create_app --factory --host 127.0.0.1 --port 8765
# 前端
cd frontend; pnpm dev --port 5173
```

（当前两个服务在线；端口被占时先 `netstat -ano | findstr :8765` 清理孤儿进程。）
