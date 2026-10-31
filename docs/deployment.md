# 生产部署与域名（topicai.online）

> 最后核对：2026-10-21。线上实测：`https://topicai.online` / `https://www.topicai.online` 返回 200，
> HSTS 生效，证书有效期至 2027-01-19。
>
> 本文只描述**生产服务器**的部署与域名/TLS；本地 Docker 验证走
> `docs/agents/wsl-docker-development.md` 的流程。

## 1. 访问入口与拓扑

```
用户浏览器
  https://topicai.online / https://www.topicai.online
        │  80 → 301 到 443；443 终止 TLS
        ▼
宿主机 nginx（宝塔自带的 nginx，运维直接维护）
  /www/server/panel/vhost/nginx/topicai.online.conf
        │  proxy_pass http://127.0.0.1:8081
        ▼
docker compose frontend 容器（topicai-frontend，nginx :80）
  /usr/share/nginx/html 静态资源 + /api 反代到 backend:8000
        ▼
docker compose backend 容器（topicai-backend，uvicorn :8000）
  只发布 127.0.0.1:8000，不直接暴露公网
  数据卷：topicai_data（SQLite/素材）、topicai_logs（日志）
```

- DNS：`topicai.online`、`www.topicai.online` 的 A 记录均指向服务器 `1.13.251.252`。
- 端口：公网只开放 `80/443`（宿主机 nginx）；frontend 容器端口 `127.0.0.1:8081` 仅绑定回环
  （宿主机 nginx 转发用，公网不可达）；`8000` 仅绑定 `127.0.0.1`；`22` SSH。
- 服务器：`ssh topicai-server`（root），源码在 `/opt/topicai`，跟踪 `main`。

## 2. 标准部署（服务器上执行）

```bash
ssh topicai-server
cd /opt/topicai
git pull --ff-only
git rev-parse HEAD                # 必须等于要部署的目标 commit
docker compose build
docker compose up -d --force-recreate
docker compose ps                 # backend 应为 healthy，frontend Up
curl -fsS http://127.0.0.1:8081/api/v2/health
curl -fsS https://topicai.online/api/v2/health
```

### 注意

- **前端镜像用 npm，不用 pnpm lock**：`frontend/Dockerfile` 执行 `npm ci`，依赖
  `frontend/package.json` + `frontend/package-lock.json`。改前端依赖时两个 lock
  （`pnpm-lock.yaml` 和 `frontend/package-lock.json`）都要更新，否则镜像构建会在
  `RUN npm ci` 失败。
- **迁移自动执行**：backend 启动时由 `backend/app/data/migrations/` 下的 `NNN_*.sql` 自动迁移。
  新增迁移时，文件库（`app/data/migrations/runner.py`）与内存库
  （`app/core/database.py` 的 `apply_migrations`）两条路径都要补 `ensure_columns`。
- 环境变量在服务器 `/opt/topicai/.env`（不入库）；升级/回滚都不要覆盖它。
- 回滚：`git checkout <上一个可用 commit> && docker compose build && docker compose up -d --force-recreate`。

### 2.1 备用部署路径：服务器无法访问 GitHub（bundle）

生产在 2026-10-31 曾遇到 `git fetch` 失败（`Failure when receiving data from the peer` / 超时）。
若确认是服务器到 GitHub 的网络问题，可在能访问 GitHub 的机器上打包**增量 bundle** 再传输：

```bash
# 本机（仓库目录；<current-prod-commit> = 生产当前 HEAD，<target> = 目标 commit）
git bundle create /tmp/update-<target>.bundle origin/main ^<current-prod-commit>
scp /tmp/update-<target>.bundle topicai-server:/tmp/

# 服务器
cd /opt/topicai
git bundle verify /tmp/update-<target>.bundle   # 必须列出 requires <current-prod-commit>
git fetch /tmp/update-<target>.bundle refs/remotes/origin/main:refs/remotes/origin/main
git merge --ff-only <target>
git rev-parse HEAD                               # 必须等于 <target>
# 之后按 §2 继续 docker compose build / up
```

- 前提：生产当前 commit 必须是 bundle 的 prerequisite（`^<current-prod-commit>`），否则校验失败。
- 传输前后用 `sha256sum` 比对 bundle；commit 一致才能继续部署。
- 网络恢复后建议 `git fetch origin` 校准 `origin/main` 远端引用。

## 3. 域名与 TLS

### 3.1 宿主机 nginx 站点配置

文件：`/www/server/panel/vhost/nginx/topicai.online.conf`（**运维直接维护，未在宝塔面板注册**；
不要用宝塔面板删除/重建该站点）：

```nginx
# HTTP：只保留 ACME 校验，其余 301 到 HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name topicai.online www.topicai.online;

    location ^~ /.well-known/acme-challenge/ {
        root /www/wwwroot/topicai.online;
        default_type "text/plain";
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS：TLS 终止 + 反代到 frontend 容器
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name topicai.online www.topicai.online;

    ssl_certificate /etc/letsencrypt/live/topicai.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/topicai.online/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS：一年。确认没有其它仅 HTTP 的子域后再考虑 includeSubDomains/preload。
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        # AI 消化/识别是长请求；容器内 nginx 已放宽到 180s，这里给足余量。
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

修改后必须校验并平滑重载：

```bash
/www/server/nginx/sbin/nginx -t
/www/server/nginx/sbin/nginx -s reload
```

### 3.2 证书

| 项 | 值 |
|---|---|
| 签发机构 | Let's Encrypt（certbot 2.8，ECDSA，ACME v2） |
| 域名（SAN） | `topicai.online`、`www.topicai.online` |
| 证书路径 | `/etc/letsencrypt/live/topicai.online/fullchain.pem` |
| 私钥路径 | `/etc/letsencrypt/live/topicai.online/privkey.pem` |
| 当前有效期 | 2026-10-21 签发，2027-01-19 到期（自动续期） |
| 校验方式 | HTTP-01，webroot `/www/wwwroot/topicai.online` |

### 3.3 自动续期

- `certbot-renew.timer`（系统 systemd timer，每 12 小时检查一次，已 enable）。
- 兜底 cron：`/etc/cron.d/certbot-renew`（每天 03:17 执行 `certbot renew --quiet`）。
- 续期后自动 reload nginx：renewal 配置里的
  `renew_hook = /usr/local/bin/reload-topicai-nginx.sh`（内容即 `nginx -s reload`）。

常用检查命令：

```bash
certbot certificates                 # 查看证书与到期时间
certbot renew --dry-run              # 续期演练（走 Let's Encrypt staging，网络慢时耗时长，失败不代表线上续期失败）
systemctl list-timers | grep certbot # 确认 timer 下次触发时间
```

## 4. 上线验证清单（2026-10-21 实测）

| 检查 | 命令 / 地址 | 结果 |
|---|---|---|
| 公网 HTTPS 健康 | `https://topicai.online/api/v2/health` | 200 `{"status":"ok","api_version":"v2"}` |
| www 域名 | `https://www.topicai.online/api/v2/health` | 200 |
| HTTP 跳转 | `http://topicai.online/content?x=1` | 301 → `https://topicai.online/content?x=1` |
| HSTS | `curl -sI https://topicai.online/` | `Strict-Transport-Security: max-age=31536000` |
| 证书 | `openssl x509 -in ...fullchain.pem -noout -subject -issuer -dates` | `CN=topicai.online`，`Let's Encrypt YE1`，至 2027-01-19 |
| 容器 | `docker compose ps` | backend healthy、frontend Up |
| 迁移 | 启动后查 `schema_migrations` / `PRAGMA table_info` | 迁移已记录、列已存在（如 059 `accepted_json`） |

## 5. 已知边界

- 宿主机 nginx 是宝塔自带实例（同时服务其它站点），本应用只是新增一个 vhost；不要在面板里
  操作该站点或覆盖该 conf。
- HSTS 目前只作用 apex 与 www；如以后增加子域，先确认全部支持 HTTPS 再加
  `includeSubDomains`/`preload`。
- `8081` 已收紧为仅回环（compose：`127.0.0.1:${FRONTEND_PORT:-80}:80`），公网只保留 80/443；
  旧书签/验收脚本请改用 `https://topicai.online`。
- 证书自动续期依赖 80 端口 ACME 路径可达；若以后 80 被拦截或重定向到别处，需改 DNS-01。
