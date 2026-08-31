# 开源仓库安全审计报告

**日期**：2026-08-31
**范围**：`wu908/topicai` 全部 git 历史（自 000 起每个提交的**曾加入内容**，含已被删除的对象）+ 当前树 + GitHub 仓库设置
**方法**：文件名全历史过滤 + pickaxe 内容扫描（7 类密钥模式）+ 高信号正则当前树扫描 + 逐 blob 验尸（对已入公开历史的二进制产物）+ 仓库设置核查
**结论**：**未发现任何 API key、令牌、私钥或凭据泄露**。个人隐私仅有两级轻微暴露（§4），可选择清理。GitHub 侧防护开关全部关闭，建议立即开启（§6，最高性价比动作）。

---

## 1. 密钥与凭据（结论：干净）

| 检查 | 结果 |
|---|---|
| `sk-`（OpenAI 兼容/DeepSeek/DashScope/Zhipu 全历史） | 0 命中 |
| AWS `AKIA`、Google `AIza`、Slack `xox`、GitHub `ghp_/github_pat_` | 0 命中 |
| `PRIVATE KEY` 块 | 0 命中 |
| 当前树高信号赋值（api_key/token/secret/password = 长字面量） | 0 命中（test/占位符除外） |
| `LLM_API_KEY` / `JWT_SECRET_KEY` / 三家厂商 key 的**历史全部增量行** | 只有占位符（`sk-your-*`）与 `${VAR:-}` 空引用 |
| `.env` 文件（根/.env、backend/.env，含本会话填入的真实凭据） | 从未入库：`.gitignore` 生效 + 全历史 diff-filter=A 无任何 `.env` 添加记录 |
| 本会话全部临时目录（.smoke-*/.upg-tmp*/.e2e-tmp*/.cov-audit） | 从未入库（历史 A 过滤验证），且 .gitignore 已加宽为 `.ci-tmp*/ .pytest-*/` 等通配 |

## 2. 曾入公开历史的测试产物（结论：无害，已修复）

提交 `eb5bd96` 曾将 `.ci-tmp-w2/w3` 下 4 个 20KB SQLite 库、1 个"PNG"、若干迁移 SQL 快照带入历史（根因：`git add backend/` 时测试临时目录已生成）。逐 blob 验尸：

- 4 个 `.db`：**全部 0 张表**（迁移测试的空库），无 users/无业务数据；
- `.png`：17 字节 ASCII 文本 `recoverable-image`（测试桩，非图片）；
- `.sql` 快照：仓库自有公开迁移文件的副本，无新增信息。

处置：HEAD 已移除（提交 `8d88449`/`37677ff`），`.gitignore` 已加宽防复发。**因内容无害，无需历史重写**。若仍希望从历史抹除，可执行 `git filter-repo --path backend/.ci-tmp-w2 --path backend/.ci-tmp-w3 --invert-paths` 后 force-push——代价是全仓 hash 变化，需要所有协作者重新克隆，本项目单人开发可接受，但不做也无实际风险。

## 3. ux-evidence 截图（低风险，建议自查）

`docs/ux-evidence/` 内 10+ 张应用 UI 截图来自测试数据（@example.com 级账号）。风险极低，建议人工快速浏览一遍确认无真实个人信息入镜。

## 4. 个人信息（两级轻微暴露，可选清理）

| 项 | 位置 | 敏感度 | 建议 |
|---|---|---|---|
| Windows 账户名 `24100`（本机路径 `C:\Users\24100\...`） | `docs/design-qa.md`、`docs/handoffs/topicai-handoff-2026-07-30-*.md`（约 4 处） | 低（数字账户名，非真名；但可关联个人机器环境） | 可保留；若求洁癖，`sed` 替换为 `<user>` 后正常提交 |
| 桌面目录结构 `E:\destop\我的\` | `docs/ai-native-async-creation-plan-2026-08-29.md` §来源 | 极低（仅目录名） | 可保留 |
| 真名/手机号/私人邮箱 | `24100`/`伍明杰`/qq/163/gmail 全历史 pickaxe | 无命中 | — |

## 5. 其他核查

- 仓库无跟踪的 `.pem/.key/.db/.sqlite`（唯一命中 `register-short-password.png` 为 UI 截图）；
- CI 日志公开可读：复核本会话工作流输出，仅打印"weak secret 警告"，无值泄露；
- E2E 本地运行的 JWT 密钥（`e2e-secret-key-for-local-run-2026`）仅存在于本地命令行，未入库。

## 6. 建议动作（按优先级）

1. **P0（设置页点两下，免费）**：GitHub → Settings → Code security → 开启 **Secret scanning**、**Push protection**（防未来误推密钥）、**Dependabot security updates**（当前三项全部 disabled）；
2. **P1**：保持 `.env` 双文件 gitignore 现状；真实凭据若曾怀疑暴露，直接在厂商控制台轮换（当前无证据需要）；
3. **P2**：§4 的文档路径清理（可选）；历史重写（可选，无必要）。
