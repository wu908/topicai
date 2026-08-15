# TopicAI Handoff - 2026-08-01 (Spec-008 US5 Review Follow-up)

> 本文档由 AI 辅助整理，依据本地 Git、测试、Docker 与两轴代码审查结果校对；未记录密钥、令牌或本地敏感配置。

工作区：`G:\codex_project\topicAI\mvp`

当前分支：`feature/explainable-opportunities`

当前 HEAD：`08f289c` — `fix: address explainable opportunity review findings`

## 当前状态

Spec-008 US5「可解释内容机会生成」由以下两个提交组成：

- `f9888f0` — `feat: implement explainable content opportunities`
- `08f289c` — `fix: address explainable opportunity review findings`

具体实现以提交及 `git diff f9888f0^...08f289c` 为准，不在本文复制。产品与治理来源见：

- [`specs/008-content-project-mvp/spec.md`](../../specs/008-content-project-mvp/spec.md)
- [`specs/008-content-project-mvp/plan.md`](../../specs/008-content-project-mvp/plan.md)
- [`specs/008-content-project-mvp/data-model.md`](../../specs/008-content-project-mvp/data-model.md)
- [`specs/008-content-project-mvp/contracts/api-v2.md`](../../specs/008-content-project-mvp/contracts/api-v2.md)
- [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md)
- [`docs/adr/0002-bound-ai-orchestration-and-learning.md`](../adr/0002-bound-ai-orchestration-and-learning.md)

`08f289c` 已逐项修复上一轮 7 条 finding，但随后对该修复提交执行的 Standards/Spec 两轴复审发现 3 个仍需处理的独立问题。当前尚未为这 3 项创建修复提交，也未在本轮执行 push 或 PR 操作。

## 待修复审查问题

### 1. P1：已执行旧版 043 的数据库得不到回填

`08f289c` 直接修改了 `backend/app/data/migrations/043_first_party_opportunities.sql`，用来补齐旧机会的 `source_trigger`、`source_refs_json` 和 `dimensions_json`。迁移 runner 对 `schema_migrations` 中已经存在的版本只记录 checksum drift 后跳过，因此曾在 `f9888f0` 上执行过 043 的数据库不会获得这些修复。

下一步应先写 RED 升级测试：构造已记录旧版 043、且仍含空来源引用/维度的数据库，再运行当前 migration runner。随后恢复 043 及其 runner 特殊处理到 `f9888f0` 版本，新增单调编号的 044 repair migration，同时覆盖 fresh DB、042 升级、old-043 升级和 replay。不要通过强制重跑已记录的 043 规避迁移纪律。

相关位置：

- `backend/app/data/migrations/043_first_party_opportunities.sql:69`
- `backend/app/data/migrations/runner.py:797`
- `backend/tests/data/test_content_project_calibration_migrations.py`

### 2. P2：过期来源返回错误码及版本检查顺序不符合契约

`ContentOpportunityService.decide()` 在 optimistic version 检查之前执行过期守卫，并抛出普通 `ValueError`。因此 stale adopt 可能返回无类型 HTTP 400，而不是 409 `VERSION_CONFLICT`；版本正确的过期请求也没有 API contract 中的稳定 `SOURCE_EXPIRED` 错误码。

下一步先增加两个 RED API 测试：stale version 必须优先返回 409；版本正确但尚未明确确认过期状态时必须返回 typed `SOURCE_EXPIRED`。先搜索并复用现有 `AppException`/错误映射模式，再做最小服务层修复。

相关位置：

- `backend/app/services/content_opportunity.py:940`
- `backend/app/core/exceptions.py`
- `backend/tests/api/v2/test_opportunities.py`

### 3. P2：前端重复实现且冻结了过期业务规则

`OpportunitiesPage` 使用列表加载时的 `checkedAt`、`expires_at` 和 `dimensions.timeliness` 重新推导 `expiredSourceNeedsConfirmation`，而后端另有一套相似规则。页面停留跨过到期时间后，UI 时钟不会更新；前后端适用范围也可能漂移。

下一步应让服务端基于服务器时间在 typed `required_action` 中表达“需要确认过期来源”，前端只渲染该契约。先增加服务/contract 测试和 UI 行为测试，再删除前端的重复时间判定；不要增加前端轮询或第二套领域规则。

相关位置：

- `frontend/src/pages/Opportunities/OpportunitiesPage.tsx:71`
- `frontend/src/types/contracts/v2/content.ts`
- `backend/app/services/content_opportunity.py`

## 已完成验证基线

以下结果是在提交 `08f289c` 后、复审前取得；代码审查本身为只读，没有改变这些文件：

- 后端定向回归：`73 passed`。
- 后端全量：`878 passed`。
- 前端机会页/API 定向：`8 passed`。
- 前端全量：`395 passed, 2 skipped`。
- Ruff、ESLint、TypeScript 与生产构建：通过。
- WSL Docker Compose build/start/health：通过；后端 health 与前端均返回 HTTP 200。
- `git diff --check`：通过。
- 验证结束后已执行 Compose `down`（未删除卷）并关闭 WSL。

修复上述 3 项后必须重新运行最小 RED/GREEN、相关回归、全量测试、静态检查、生产构建和提交前 WSL Compose 健康检查。

## 工作区注意事项

`08f289c` 只提交了 13 个产品/测试文件。当前工作树仍包含用户已有的 `AGENTS.md` 修改，以及 `docs/agents/`、`docs/handoffs/` 下多份未跟踪文档；这些不属于该修复提交。不要批量暂存、覆盖、删除或提交它们。

本交接文件本身也是未跟踪项目文档，是否与后续修复一起提交必须由用户单独确认。

开发与容器操作遵循 [`AGENTS.md`](../../AGENTS.md) 的 Windows-source、WSL-first 规则；不得执行 `docker compose down -v`。

## 建议执行顺序

1. 用 TDD 修复 old-043 → 044 数据升级路径，并单独验证 migration replay。
2. 用 typed exception 修复 `VERSION_CONFLICT` 优先级和 `SOURCE_EXPIRED` 契约。
3. 把过期确认状态集中到后端 `required_action`，删除前端重复判断。
4. 运行相关回归及全量门禁，再执行 `code-review` 审查新的修复提交。
5. 用户确认后再 commit；显式列出文件，继续排除已有 `AGENTS.md` 与其他 handoff 文档。

## Suggested skills

- `tdd`：三个 finding 都应先建立可复现 RED，再做最小修复。
- `diagnose`：若 old-043 fixture、错误映射或前后端 contract 出现非预期行为，用系统化诊断定位根因。
- `code-review`：修复提交完成后继续按 Standards/Spec 两轴复审。
- `handoff`：下一阶段结束时更新状态；引用本文件、提交和规范，不复制 diff。

