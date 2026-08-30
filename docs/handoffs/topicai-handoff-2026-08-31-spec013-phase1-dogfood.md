# TopicAI 交接：Spec-013 Phase 1 交付 + 狗粮期测试启动

> 日期：2026-08-31
> 分支：`main`（本地领先 origin 3 个提交，见 §2 紧急事项）
> 上一份全景：`docs/topicai-project-development-retrospective-2026-08-18.md`
> 本文档目的：让新会话/新代理**不开历史聊天**即可继续工作。

---

## 1. 当前状态快照

- 产品方案：**异步创作循环**（收件箱→生产→拾取→发布→周复盘），方案与七轮质询决议见
  `docs/ai-native-async-creation-plan-2026-08-29.md`（唯一权威，含三条证伪线与分阶段计划）。
- 设计规范：**DESIGN.md v3「琉璃 Lumen」**（仓库根）——科幻半透明白玻璃、无绿、
  悬浮球+π 形灯框+独立输入泡、GSAP 四幕入场。前端实现的唯一设计权威。
- 规格：`specs/013-async-creation-loop/`（spec / data-model / tasks，Phase 1 全勾选）。
- 后端：迁移 **050**（四表）+ **051**（precheck_json）；服务 `app/services/async_loop.py`
  （Inbox/Production+PublishCheck/Pickup/LoopMetrics）+ `weekly_review.py`；路由
  `app/api/v2/async_loop.py`（/loop/inbox、/deliverables、:pickup、:discard、/weekly、/metrics）。
- 前端：`/loop` 页（收件箱/产出架+拾取/周复盘区块/证伪线度量），路由与侧栏导航「创作循环」已挂。
- 测试：后端 **384 passed / 88.46%**；前端 **222 passed** / lint / build 绿；
  E2E `frontend/e2e/async-loop.spec.ts` **2 passed**（真实栈 8765+5173）。
- CI：截至 `eb5bd96` 全绿；本地修复提交（b821f6d、8d88449、37677ff）与文档提交（1bfcd6c）
  **尚未推送**，推送后需确认 CI（见 §2）。

## 2. 紧急事项（下一会话第一件事）

**本地领先 origin 3 个提交未推送**：`1bfcd6c`（狗粮测试方案）、`8d88449` 与 `37677ff`
（清理 eb5bd96/051-era 意外带入的 `.ci-tmp-w2/w3` 临时产物并加宽 .gitignore）。
推送失败原因：本地代理（127.0.0.1）当时离线。行动：确认代理在线 →
`git push origin main` → 观察 CI 至绿。**预期 CI 绿**（本地全量测试与 ruff 均已过；
此前 5c544ea 的 CI 红是 ruff UP017/I001，已在 b821f6d 修复并绿）。

## 3. 关键决策与纪律（只列指针，细节在文档内）

- 三条证伪线与判定规则（2 线不达即回炉）：狗粮协议 §1；
  测试执行协议（记录表 A/B/C、防走样条款）：`docs/testing/dogfood-falsification-protocol.md`。
- **分阶段门控**：Phase 2 狗粮期由**产品负责人/测试者执行**（两周）；Phase 3 陪伴层与
  Phase 4 成长层**被 Phase 2 证据门控**——达标才开工，不达标先回炉。代理不得擅自跳过。
- PublishCheck 是生产承重墙：预检不过不产 ready（needs_input 事件、素材留箱）。
- 事实逐条溯源到收件箱条目；私密素材（consent=private）永不进生产。
- 拾取必须走 `ContentProjectService.create` + `IntentConfirmationService.confirm`
  （PR #23 教训）；四决策 HumanGate 不可绕过。
- 动效编排用 GSAP（官方技能已装：gsap-core/timeline/plugins/performance/react/scrolltrigger/utils/frameworks），
  环境循环归 CSS；`prefers-reduced-motion` 全量降级。

## 4. 环境变更备忘（本会话发生）

- **WSL 已重装**：发行版经 `wsl --import-in-place Ubuntu F:\wsl\Ubuntu\ext4.vhdx` 原地恢复，
  docker 引擎可用（旧镜像保留）。注意：本机 WSL 挂载 vhdx **需要管理员上下文**——
  容器验证按 `$windows-wsl-docker-validation` 走提权包装，每次一次 UAC。
- `backend/.env` 已由用户填入真实 LLM 凭据（真实模型 smoke 已过：AI 路径 13/14 +
  降级路径 14/14）。测试套件已对此免疫（conftest 强制重读 Settings 单例），勿删除该文件。
- Playwright chromium 已安装（E2E 可直接跑；后端需手动起在 8765，配置不自动拉起）。
- 三个本地 .env：`backend/.env`（本地跑后端+真实模型）、mvp 根 `.env`（Docker，LLM 键已同步）、
  均已 gitignore。

## 5. 已知问题 / 待办（按优先级）

1. 推送 §2 的 3 个提交并看 CI（唯一阻塞项）。
2. Phase 2 狗粮期启动：按协议招募 3–5 位真实创作者（标准 §2），Day 0 环境、
   两周执行、Day 14 按三条线判定；记录表模板在协议 §5。
3. Phase 1 小尾巴（可选，低风险）：周复盘行的"确认动作"目前深链到项目工作台，
   可再做一屏内编排（驱动既有门控端点，不得绕行）。
4. 设计系统全局迁移：`frontend/src/styles/theme.ts` 仍为旧 v4 主题，/loop 页是
   局部 Lumen 样式；全局迁移按 DESIGN.md §2–§4 令牌做，是独立提交序列。
5. `users.ai_calls_today` 计数器未接在候选生成路径（smoke 发现），确认废弃或接线。
6. mypy 本机被 Windows 应用控制策略阻止（DLL 被拦）——CI Linux 正常；本地用 ruff 替代把关。

## 6. 下一会话建议焦点

按 §5 顺序：推送→CI→狗粮启动材料就绪。**若用户跳过狗粮要求直接开建 Phase 3/4**，
先引用狗粮协议 §7 的判定规则提醒门控，得到用户明确豁免后再动工。

## 7. 建议技能（Suggested skills）

- `handoff`（本文档技能；下次交接沿用）
- `gsap-timeline` / `gsap-core`（陪伴层动效编排；官方技能已装于用户技能目录）
- `design-taste-frontend` + `stitch-design-taste`（新界面/组件按其判读与 Pre-Flight 纪律）
- `windows-wsl-docker-validation`（容器复验；注意本机需提权跑 WSL）
- `redesign-existing-projects`（若狗粮证据触发方向回炉，按其审计-诊断-修复流程走）

## 8. 本会话提交清单（旧→新）

f8e520e DESIGN v2.1（悬浮球对话）→ 7c32d49 DESIGN v3 + Spec-013 → 44200fb 后端骨架 →
e7fd7ac 前端三屏 → 5c544ea 周度复盘+E2E → b821f6d CI 修复 → eb5bd96 PublishCheck+急稿 →
1bfcd6c 狗粮协议 → 8d88449/37677ff 临时产物清理（**后三者待推送**）。
另有早前已推：214a048 复盘文档、c4637a1 异步循环方案+词汇表。
