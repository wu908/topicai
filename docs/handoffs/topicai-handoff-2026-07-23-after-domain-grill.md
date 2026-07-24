# TopicAI 交接文档：Phase 21 与领域决策

**日期**：2026-07-23  
**仓库**：`G:\codex_project\no_1_project\mvp`  
**当前分支**：`agent/phase-21-calibration-completeness`

## 1. 现在做什么

当前正在收尾并交付两个连续增量：

- Phase 20：自动化合成验收矩阵，已经形成本地提交 `13e5ca9`。
- Phase 21：校准完整性实现已经完成，但仍在工作区中，尚未提交。

Phase 21 之后又完成了仓库级 agent 配置与一次
`grill-with-docs` 领域访谈。这些文档同样尚未提交。

此时不要继续写新业务代码。当前目标是先审查、拆分提交、推送、PR、
等待 CI 并合并，再从最新 `main` 开始意图模型迁移。

## 2. 已经完成了什么

### Phase 20 与 Phase 21

Phase 20 已提交，但尚未进入 `origin/main`。

Phase 21 已完成 T034、T036、T039、T042。实现与边界见：

- `specs/009-ai-native-action-loop/phase-21-calibration-completeness.md`
- `specs/009-ai-native-action-loop/tasks.md`
- `specs/009-ai-native-action-loop/data-model.md`

最近一次完整后端门禁：

- `803 passed`
- `1 deselected`
- 覆盖率 `86.95%`
- `git diff --check` 通过

不要在交接文档中重新推断 Phase 21 行为，以其阶段文档和实际 diff 为准。

### Agent 配置

`setup-matt-pocock-skills` 已完成：

- `CLAUDE.md` 增加一个 `## Agent skills` 块。
- `docs/agents/issue-tracker.md` 使用 GitHub Issues。
- `docs/agents/triage-labels.md` 使用默认五类标签。
- `docs/agents/domain.md` 使用 single-context 布局。

### 领域模型

`grill-with-docs` 已完成 36 个逐项确认。共同语言与关键决策见：

- `CONTEXT.md`
- `docs/adr/0001-root-publication-work-in-content-intent.md`
- `docs/adr/0002-bound-ai-orchestration-and-learning.md`

关键结论已经确认，但尚未进入 Spec 或生产代码。不要把 ADR 描述误认为
当前实现已经满足。

## 3. 卡在哪里

没有外部技术阻塞，当前卡点是交付顺序与模型迁移边界：

1. 工作区混有 Phase 21 代码、agent 配置、领域词汇表、ADR 和交接文档。
   它们需要逻辑拆分提交，不能做成一个无法审查的提交。
2. 当前分支基于 Phase 20 本地提交；`origin/main` 还没有 Phase 20。
   当前 PR 必然同时包含 Phase 20 与 Phase 21。
3. 新确认的领域模型与现有契约存在明确差距：
   - 所有意图仍强制 `audience_problem` / `reader_promise`。
   - 复盘仍强制同时生成 continue / stop / experiment。
   - 自动准备仍使用全局 `3 项目 + 80%` 信任条件。
   - Creator Series 仍限制相同意图和形式。
   - 少于三个可比样本仍可能生成观察范围位置。
4. `CLAUDE.md` 原正文仍是历史 v4.1 方案；只新增了 agent 配置块。
   当前实施规范以 `AGENTS.md` 和 Spec 009 为准。
5. PowerShell 会阻止 `codegraph.ps1`。使用
   `G:\nodejs\node_global\codegraph.cmd explore "..."`。

## 4. 下一步做什么

1. 使用 CodeGraph、`code-review` 和 `ponytail:ponytail-review` 审查
   `origin/main..HEAD` 及当前未提交 diff。
2. 不改代码时无需重复五分钟完整测试；若审查产生代码修改，重新运行后端
   CI 等价命令和 `git diff --check`。
3. 至少拆成两个逻辑提交：
   - Phase 21 实现、测试、迁移和 Spec 009 完成证据。
   - agent 配置、`CONTEXT.md`、ADR 与交接文档。
4. 推送 `agent/phase-21-calibration-completeness`，使用 GitHub 插件创建
   PR、审查检查、等待 `ci-backend` 与 `ci-frontend`，然后合并。
5. 合并后从最新 `main` 新建分支，先写下一份迁移 Spec，不直接改代码。
6. 新 Spec 的首个垂直切片应是：
   - 意图中立的 Publish Judgment 公共骨架
   - `solve/share/record` 专属必填声明
   - 工作意图确认与 Intent Lock 分离
   - 旧数据保持 `legacy/unclassified`，不默认映射为 `solve`
7. 契约、迁移、后端、前端和测试顺序确定后，再开始实现。

## 5. 哪些坑不要踩

- 不要 reset、checkout 或清理当前脏工作区。
- 不要把新领域迁移塞进 Phase 21 分支。
- 不要删除或原地改写已锁定的 Publish Judgment；使用兼容迁移和追加记录。
- 不要把旧内容默认归为 `solve`。
- 不要恢复所有意图通用的“问题/答案”表单。
- 不要把平台指标解释为成功、因果或涨粉预测。
- 不要用少于三个样本或不匹配的观察窗口生成历史范围判断。
- 不要让热点或新闻替代 Creator Anchor。
- 不要把能力级授权重新压成全局信任分。
- 不要自动发布、自动公开、自动确认事实或自动写入长期经验。
- 不要提交密钥、数据库、上传文件、缓存、`.ci-tmp` 或生成产物。
- 仓库保持私有。
- 本机 GitHub 网络曾不稳定，PR、检查与合并优先使用 GitHub 插件。

## 建议 Skills

- `code-review`：审查 Phase 20 与 Phase 21。
- `ponytail:ponytail-review`：检查重复机制和过度设计。
- `github:yeet`：确认提交边界后发布本地改动。
- `github:github`：处理 PR、检查与合并。
- `github:gh-fix-ci`：仅在 Actions 失败时使用。
- `request-refactor-plan`：为下一份意图模型兼容迁移制定最小步骤。
- `domain-modeling`：后续术语发生真实变化时维护 `CONTEXT.md`。

## 敏感信息

本文未包含 API 密钥、密码、邮箱、令牌或其他个人身份信息。

