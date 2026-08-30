# Spec-013：异步创作循环（收件箱-生产-拾取）

**状态**：Phase 1 步行骨架实施中
**依据**：`docs/ai-native-async-creation-plan-2026-08-29.md`（已拍板方案）+ `DESIGN.md` v3 + 七轮质询决议
**宪法**：所有 HumanGate 红线、AITrace、`/api/v2` only、additive migration、TDD ≥80% 覆盖、无死路降级——沿用 `.specify/memory/constitution.md` 与 ADR-001/002/003。

## 1. 目标（Phase 1 步行骨架）

创作者把灵感/素材丢进**收件箱**；**生产线程**（无模型时确定性降级）把收件箱消化为**产出（Deliverable）**；创作者在**产出架**上**拾取**（选择即确认事实清单 + 定时），拾取即建 ContentProject；发布后走既有**周度批确认**复盘。陪伴/成长层不在本期。

## 2. 需求（Phase 1）

- FR-1 收件箱：添加（text/image/voice/link/idea 五类 + 授权标记 publishable/private，默认最小）、列表、幂等；私密素材不进入生产。
- FR-2 生产线程：状态机 queued→producing→ready / failed(重试≤2→needs_input)→expired(7 天)；货架限流（ready<6 才生产）；**探索位**：每批含 1 条 idea 派生尝试；无模型走确定性骨架（沿用降级纪律）；每次生产写 AITrace（task_type=`inbox_production`，无模型 capability=deterministic_fallback）。
- FR-3 产出（Deliverable）：标题/大纲/正文/**事实清单（逐条溯源到收件箱条目）**/发布判断草案/建议发布时点/意图（AI 拟 solve|share|record）；缺证据不产 ready。
- FR-4 拾取：POST pickup（选择即确认 + schedule_at）→ 复用 `ContentProjectService.create` + `IntentConfirmationService.confirm()` 建项目（吸取 PR#23 教训：共享语义必须走正式服务入口）；幂等；二次拾取拒绝。
- FR-5 落选：discard(归因 reason) → 记偏好事件 + 回灵感池语义（状态 discarded）。
- FR-6 过期：ready 7 天未拾取自动 expired（sweep 方法）。
- FR-7 度量：loop_metrics 事件表记录 pickup 耗时、发布数、周维护时长输入点（三条证伪线数据）。
- FR-8 所有写操作带 idempotency_key + expected_version（沿用既有契约纪律）。

## 3. 边界（本期不做）

陪伴话术/晨报生成、信任面板、漂移提议 UI、探索位面板、急稿前端（沿用现有引导流）、周复盘批量接口（Phase 1.5）、vision/语音转写（素材仅存与溯源）。

## 4. 验收

- 后端全量测试绿（既有 360+ 不降）+ 新增覆盖 ≥80%。
- 无模型环境全流程可用（确定性骨架产出）。
- 探索位落选不扣任何信任/评分（本期无信任系统，仅为后续预留语义）。
- 事实溯源：deliverable.facts_json 每条含 source_inbox_id。
