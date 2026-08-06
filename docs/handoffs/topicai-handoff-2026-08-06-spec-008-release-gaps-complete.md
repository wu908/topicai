# TopicAI Handoff - 2026-08-06 (Spec 008 Release Gaps Complete)

> 本文档由 AI 辅助整理，依据本地差异、自动化测试、运行时 OpenAPI 和隔离 Docker 验证校对；不包含密钥、令牌或用户运行数据。

工作区：`G:\codex_project\topicAI\mvp`
分支：`008-content-project-mvp-completion`

## 当前状态

Spec 008 的本轮发布缺口与发布审计修复已完成并通过本地发布门禁。运行时只保留 `/api/v2`；历史迁移保留用于升级，最新迁移为 `048_release_audit_fixes`。

本轮补齐：

- 素材的文本、链接、图片、文档、隐私、项目引用和安全删除。
- 设置页的周目标、内容策略、小红书账号备注和 AI 能力状态。
- 版本绑定的发布检查、逐条确认、发布素材导出和单项重试。
- 截图指标提取提案，用户确认前不写入已确认指标。
- 账户数据导出和删除的持久化审计 job；本地 MVP 同步完成，不增加队列或 worker。
- `DELETE /api/v2/account` 返回 `202` envelope；导出结果包含完成态 `job`。
- 账户删除先撤销凭据；登录、刷新令牌和当前用户查询都拒绝已撤销账户。
- 账户导出包含项目状态事件、文件状态和 Base64 文件本体。
- 截图提取保存用户决策并关联最终性能快照；Material API 不泄露内部存储字段。
- 生成并同步 81-path 的 `backend/openapi3.json`，其中没有 `/api/v1`。
- 增加 v2 禁止源/预测字段扫描与严格 UTF-8/乱码扫描，并接入 CI。

## 关键设计边界

- 账户删除后只保留最小操作审计：job ID、原 owner UUID、操作、状态和时间。
- 发布检查绑定不可变内容版本；确认原始 findings 不被改写。
- 发布素材按 artifact 独立重试，已完成项不重复生成。
- AI 继续使用 OpenAI-compatible 配置；无模型和无 vision 能力时保留手动路径。
- React Router 不跨主版本升级；v7 迁移留给独立变更。

## 验证结果

- 后端全量：281 passed，coverage 87.60%。
- 迁移：全量套件通过；Docker fresh 与 `047 -> 048` upgrade 均通过。
- Ruff：通过。
- mypy `--no-site-packages`：97 source files，无问题。
- Bandit high/critical：0。
- 前端 Vitest：25 files、141 passed，line coverage 80.34%。
- 前端 lint、TypeScript、production build：通过。
- Playwright Chromium：3 passed。
- pnpm high audit：通过；保留 3 个 moderate React Router advisory。
- Docker fresh-volume：frontend/backend healthy，HTTP 200，OpenAPI 81 paths/0 v1，048 已应用，重启后用户可登录。
- Docker upgrade：047 旧用户升级后保留并可登录，048 只应用一次。
- 两个 Docker 验证项目的容器/网络已由普通 `docker compose down` 移除；四个隔离卷和四个任务镜像也已显式删除，基础镜像与构建缓存保留。
- Starter/Growth 真实后端 Playwright、离线恢复、1440x900 与 390x844 溢出/重叠检查通过。

完整命令和证据见 `specs/008-content-project-mvp/release-validation.md`。

## 工作树边界

本次提交只应包含本轮实现、测试、Spec/README/OpenAPI、发布验证和本交接文档。以下用户已有文件不属于本次提交：

- `backend/uv.lock`
- `docs/agents/wsl-docker-development.md`
- 其他未跟踪的 `docs/handoffs/*.md`

不得使用 `git add .`。

## 已知非阻断项

- React Router v6 的 3 个 moderate advisory 需要破坏性的 v7 升级，本轮不处理。
- Bandit 仍报告既有 low/medium 动态 SQL 启发式结果；high/critical 为 0。
- WSL 偶发 systemd user-session warning，但 Docker 构建、健康检查和重启验证均通过。
- 应用内 Browser 插件的本机 kernel-assets 路径缺失；已用仓库 Playwright 完成等价运行时 QA。
