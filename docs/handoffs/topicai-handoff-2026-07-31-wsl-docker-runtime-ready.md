# TopicAI Handoff - 2026-07-31 (WSL Docker Runtime Ready)

> 本文档由 AI 辅助整理，并依据本地 WSL、Docker、Git 和 HTTP 验证结果校对。敏感配置值已省略。

工作区：`G:\codex_project\topicAI`

Git 根目录：`G:\codex_project\topicAI\mvp`

当前分支：`feature/growth-onboarding-history-profile`

## 当前状态

TopicAI 已通过 Ubuntu WSL2 内的 Docker Engine 成功运行，不依赖 Docker Desktop。当前按需运行策略已生效：容器、保活进程和 WSL 均已停止，日常不占用 WSL 内存。启动后可访问：

- 前端：<http://localhost>
- API 文档：<http://localhost:8000/docs>
- 后端健康检查：<http://localhost:8000/api/v1/health>
- `/api/v2/projects` 已出现在 OpenAPI。

当前运行版本：

- WSL：`2.6.1.0`
- Ubuntu：`26.04 LTS`
- Docker Engine：`29.1.3`
- Docker Compose：`2.40.3`

项目业务状态和已合并功能不要在本文重复推断，继续参考：

- [`topicai-handoff-2026-07-31-growth-onboarding-history-profile-merged.md`](./topicai-handoff-2026-07-31-growth-onboarding-history-profile-merged.md)
- [`topicai-handoff-2026-07-31-project-state-event-merged.md`](./topicai-handoff-2026-07-31-project-state-event-merged.md)
- [`specs/008-content-project-mvp/plan.md`](../../specs/008-content-project-mvp/plan.md)
- [`specs/008-content-project-mvp/quickstart.md`](../../specs/008-content-project-mvp/quickstart.md)

## Docker 与存储布局

Ubuntu WSL 发行版注册在 `G:\ubuntu`，其虚拟磁盘为 `G:\ubuntu\ext4.vhdx`。Docker 默认数据目录是 `/var/lib/docker`，因此 Docker 程序、镜像、容器和命名卷均实际存放在 G 盘的 WSL 虚拟磁盘中。

辅助目录：

- Docker 安装包：`G:\Docker\Installer`
- Docker 代理配置源文件：`G:\Docker\Installer\docker-proxy.conf`
- Docker Desktop 安装包已下载但未安装；当前运行环境不需要 Docker Desktop。

曾出现 `Wsl/Service/CreateInstance/MountDisk/HCS/E_ACCESSDENIED`。根因是当前 Windows 账户对 `G:\ubuntu\ext4.vhdx` 缺少显式完全控制权限。已通过管理员授权为当前账户补充该权限，WSL 随后恢复正常。不要注销、移动或重建该发行版来处理同类问题，先检查 VHD ACL。

## 网络与代理

Windows 系统代理只监听 `127.0.0.1:18780`。为让 WSL 和 Docker 使用该代理，已创建用户级配置 `C:\Users\<user>\.wslconfig`：

```ini
[wsl2]
networkingMode=mirrored
autoProxy=true
dnsTunneling=true
firewall=true
```

Docker 服务代理安装在：

```text
/etc/systemd/system/docker.service.d/proxy.conf
```

代理配置中不含认证凭据。修改 Windows 代理端口后，需要同步修改 `G:\Docker\Installer\docker-proxy.conf`，重新安装到上述 systemd 路径，然后执行：

```powershell
wsl -d Ubuntu -u root -- systemctl daemon-reload
wsl -d Ubuntu -u root -- systemctl restart docker
```

## 项目本地配置

已创建被 Git 忽略的 `G:\codex_project\topicAI\mvp\.env`：

- 使用随机生成的本地 JWT 密钥，本文不记录其值。
- `LLM_*` 和旧供应商 API key 均为空。
- 当前以无 AI 的手动降级路径运行。
- `CONTENT_PROJECT_V2_ENABLED=true`，`AI_ENABLED=true`，`VISION_ENABLED=false`。

不要提交或复制该 `.env`。

## 为 Docker 构建所做的未提交改动

首次构建暴露了两个仓库问题，已做最小修复：

- 新增 [`backend/.dockerignore`](../../backend/.dockerignore)，避免发送 `.venv`、缓存和本地运行数据。
- 新增 [`frontend/.dockerignore`](../../frontend/.dockerignore)，避免发送 `node_modules`、`dist` 和覆盖率目录。
- 更新 [`frontend/package-lock.json`](../../frontend/package-lock.json)，使其与镜像内 Node 22 / npm 10 的 `npm ci` 兼容。
- 从 [`backend/requirements.txt`](../../backend/requirements.txt) 和 [`backend/pyproject.toml`](../../backend/pyproject.toml) 移除未被生产代码使用的 `sentence-transformers` 与可选 `chromadb`，从依赖树消除 PyTorch、CUDA、Triton 和 Transformers。
- 新增 [`backend/requirements-dev.txt`](../../backend/requirements-dev.txt)，测试和质量工具不再进入生产镜像。
- 更新 [`backend/Dockerfile`](../../backend/Dockerfile)，移除 `build-essential`，只安装健康检查需要的 `curl`。
- 更新 [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)，CI 改为安装 `requirements-dev.txt`。

这些文件尚未提交。当前工作区还包含多份用户已有、未跟踪的 `docs/handoffs/` 文档；不要删除、覆盖或批量提交它们。

## 验证结果

- `docker run --rm hello-world`：通过，证明 Docker Hub 拉取和容器运行正常。
- `docker compose up --build -d`：通过。
- 后端容器：`healthy`。
- Windows 访问 `http://127.0.0.1:8000/api/v1/health`：返回 `200` 和 `status=ok`。
- Windows 访问 `http://127.0.0.1/`：返回 `200`。
- OpenAPI：包含 `/api/v2/projects`。
- 前端 `npm ci` 和生产构建：通过。
- 新后端镜像：`508 MB`，原镜像约 `9.47 GB`。
- 镜像内 `torch`、`sentence_transformers`、`chromadb` 和 `pytest`：均不存在。
- 新镜像启动、Compose `--wait`、健康检查及关闭流程：通过。
- 开发依赖 `pip install --dry-run -r requirements-dev.txt`：通过。
- `git diff --check`：通过。

未运行完整后端/前端测试套件。本轮目标是验证 WSL Docker 运行路径，而不是重新执行发布门禁。

前端构建报告现有依赖包含 `2 moderate + 3 high` 共 5 个 npm 漏洞，未阻塞本地启动；后续应单独审计，不要直接运行可能引入破坏性升级的 `npm audit fix --force`。

## 运行与恢复

不再使用隐藏保活进程，也没有计划任务或启动目录项。需要使用时，在 PowerShell 打开交互式 Ubuntu，并在使用期间保持该终端开启：

```powershell
wsl -d Ubuntu
```

在 Ubuntu 终端中启动项目：

```bash
cd /mnt/g/codex_project/topicAI/mvp
docker compose up -d
```

查看状态：

```bash
docker compose ps
```

不用时在同一 Ubuntu 终端中停止项目并退出：

```bash
docker compose down
exit
```

必要时在 PowerShell 执行 `wsl --shutdown`，可立即确保 WSL 和 `vmmemWSL` 完全退出。不要使用 `docker compose down -v`，否则会删除命名卷数据。

## 空间风险

旧 PyTorch/CUDA 镜像和构建缓存已清除，共回收 Docker 内部空间约 `10.63 GB`。随后使用 Windows 标准 VHD 压缩：

- `G:\ubuntu\ext4.vhdx`：从约 `18.9 GB` 降至 `4.32 GB`。
- G 盘可用空间：从约 `7.92 GB` 回升至 `22.51 GB`。
- 当前 Docker 镜像合计约 `822 MB`，其中后端 `508 MB`、前端 `93.6 MB`、Node 构建镜像 `232 MB`。

不要执行 `docker compose down -v`，除非明确要删除本地数据库和命名卷数据。清理前先检查：

```powershell
wsl -d Ubuntu -- docker system df
```

VHD 压缩脚本保存在 `G:\Docker\Installer\compact-ubuntu-vhd.txt`。再次压缩前必须先执行 `wsl --shutdown`，确保发行版处于 Stopped 状态。

## 建议下一步

1. 将 `.dockerignore` 和锁文件修复作为独立提交审查，不要混入现有未跟踪交接文档。
2. 运行完整后端测试和 npm 安全审计后，再将 Docker/依赖优化提交 PR。
3. 后续继续按需启动 WSL，不新增保活或登录自启动任务。

## Suggested skills

- `diagnose`：排查 WSL 挂载、代理、容器重启或 Windows localhost 不可达问题。
- `code-review`：审查 `.dockerignore`、锁文件变化和后续 CPU-only 镜像修改。
- `codex-security:security-diff-scan`：评估 npm 漏洞及依赖调整的安全影响。
- `ponytail:ponytail`：保持 Docker 修复范围最小，避免同时重构依赖体系或部署架构。
- `handoff`：完成下一阶段后继续生成紧凑交接，并引用本文件而非重复环境说明。
