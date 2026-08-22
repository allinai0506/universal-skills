---
name: xiyu-server-deploy
description: 西域数智化投标管理平台（XiYu）服务器部署工作流 — 在西域项目内（~/xiyu/** 任意目录、xiyu worktrees 如 trae/zcode/cursor/claude/gemini/mimo/minimax/grok/qoder/kimi 下）触发。触发词：部署服务器、发布上线、生产部署、prod rollout、服务器更新、西域部署、xiyu deploy、部署前后检查、部署报告、回滚预案、数据库迁移 MySQL 8.0、smoke 检查 API、服务器验证、服务器故障排查。调用时机：部署前预检（preflight）、备份旧版 artifact、激活新 jar/docker、执行健康检查 + API smokes、生成发布报告、回滚规划、排查上线异常。⚠ 仅西域项目可用：若当前工作区不在 ~/xiyu/ 下或不处于 xiyu* 目录族（含 xiyu/worktrees/*），必须自抑制（SELF-INHIBIT）：禁止执行任何 ssh/scp/curl 服务器命令，并立即告知用户「本技能只在西域数智化投标管理平台 (XiYu) 项目内可用」。
---

# XiYu Server Deploy (XiYu Project Exclusive)

## Operating Contract

> **PROJECT GATE (HARD):** This skill is exclusively locked to xiyu* projects. Before taking ANY action, verify that the current workspace/project path is under `~/xiyu/` or the project directory name starts with `xiyu`. If NOT, immediately STOP and respond that this skill can only be used within the 西域数智化投标管理平台 (XiYu) project. No ssh/scp/curl to any server is permitted outside of XiYu.

Treat the 西域数智化投标管理平台 deployment path as real API only:

- Use `VITE_API_MODE=api` and real backend integration for build, smoke, UAT, screenshots, and acceptance.
- Use MySQL 8.0 for production with `SPRING_PROFILES_ACTIVE=prod,mysql` and `DB_ENGINE=mysql`.
- Do not add or depend on mock/demo/local-memory deployment paths.
- Treat deployment as a closed loop: preflight, backup, artifact activation, health check, smoke verification, report, and rollback readiness.

For detailed variables, scripts, and checklists, read `references/release-runbook.md` when the user asks for exact deployment steps, server setup, GitHub Actions configuration, production verification, or rollback commands.

## 环境选择（硬门禁 — 每次部署强制执行）

> **此门禁不可跳过。未通过门禁确认目标环境之前，AI 必须拒绝执行任何 scp、ssh、curl 到服务器的命令。**

### 环境对照表

| 环境 | ENV 值 | 主机名 | IP | 用途 |
|------|--------|--------|-----|------|
| 测试 | `test` | `winbid-01` | `172.16.38.78` | 日常部署验证、功能测试 |
| 生产 | `prod` | `winbid-01` | `172.16.10.149` | 正式环境、对外服务 |

### 门禁流程（每次部署前强制执行）

```
Step 0.0  用户声明环境：ENV=test 或 ENV=prod
Step 0.1  AI 打印目标环境确认信息（IP、主机名、用途）
Step 0.2  AI 使用 AskUserQuestion 工具要求用户确认："确认部署到 [环境名] (IP)？"
Step 0.3  用户选择 "确认" → 继续；选择 "取消" → 终止部署
Step 0.4  AI 设置 TARGET_HOST 变量，所有后续命令使用该变量
```

**如果用户未声明 ENV，AI 必须主动询问，不得自行假设。**

### 确认模板

AI 在执行任何部署操作前，必须使用 AskUserQuestion 工具展示以下信息：

```
问题: "确认部署目标环境？"
选项:
  - "确认：测试环境 172.16.38.78" (description: "winbid-01 测试服务器，已部署 82 次+")
  - "确认：生产环境 172.16.10.149" (description: "winbid-01 生产服务器，⚠️ 这是正式环境")
  - "取消部署" (description: "终止本次部署操作")
```

## Target Environment

### 双环境通用配置（测试 & 生产一致）

| 项目 | 值 |
|---|---|
| SSH user | `jetty` |
| App root | `/opt/xiyu-bid` |
| Frontend public dir | `/srv/www/xiyu-bid`（所有权 `nginx:nginx`，需 sudo 操作） |
| Backend jar | `/opt/xiyu-bid/shared/backend/app.jar` |
| Backend service | `xiyu-bid-backend`（systemd） |
| Backend internal port | `18080`（由 `/etc/xiyu-bid/backend.env` 的 `SERVER_PORT` 决定） |
| Nginx external port | `80` / `8080`（代理到后端 `18080`） |
| Backend env file | `/etc/xiyu-bid/backend.env`（`sudo` 读取） |
| Flyway repair runner | `/opt/xiyu-bid/bin/flyway-repair-runner.sh` |
| DB backups | `/opt/xiyu-bid/db-backups/` |
| Releases | `/opt/xiyu-bid/releases/<release-id>/` |
| Incoming | `/opt/xiyu-bid/incoming/` |
| Deployed record | `/opt/xiyu-bid/deployed-release.json` |

### 环境差异（测试 vs 生产）

| 项目 | 测试 (`ENV=test`) | 生产 (`ENV=prod`) |
|---|---|---|
| TARGET_HOST | `172.16.38.78` | `172.16.10.149` |
| MySQL | `winbid-01.test.rds.ehsy.com:3306` | 从 `/etc/xiyu-bid/backend.env` 读取 |
| Redis | `winbid-01.test.redis.ehsy.com:6379` | 从 `/etc/xiyu-bid/backend.env` 读取 |
| 部署历史 | 82 次+ | 8 次 |
| 基础设施 | 完整（Java 21 + Nginx + MySQL） | 完整（Java 21 + Nginx + MySQL） |

服务器连通性探测：
```bash
# ENV=test
ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 jetty@172.16.38.78 'hostname; date; whoami'
# ENV=prod
ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 jetty@172.16.10.149 'hostname; date; whoami'
```

> 以下所有命令示例中的 `${TARGET_HOST}` 在 test 环境替换为 `172.16.38.78`，在 prod 环境替换为 `172.16.10.149`。

## 生产环境首次初始化（历史参考）

> **当前生产环境 `172.16.10.149` 已完成初始化并部署 8 次，本节仅作为新服务器初始化参考。**
> 测试环境（`ENV=test`）已有完整基础设施，跳过此步骤。

首次初始化前状态（2026-07-09 首次探测记录）：
- OS: CentOS/RHEL（`/dev/vda1` 99G）
- Java: 1.8.0_231（需要升级到 Java 21）
- Nginx: 未安装
- `/opt/xiyu-bid/`: 不存在
- `/etc/xiyu-bid/`: 不存在
- systemd 服务: 无

### 初始化步骤

```bash
# 1. 安装 Java 21
sudo yum install -y java-21-openjdk java-21-openjdk-devel
# 或使用 Amazon Corretto 21
# sudo rpm --import https://yum.corretto.aws/corretto.key
# sudo curl -L -o /etc/yum.repos.d/corretto.repo https://yum.corretto.aws/corretto.repo
# sudo yum install -y java-21-amazon-corretto-devel

# 2. 安装 Nginx
sudo yum install -y epel-release
sudo yum install -y nginx
sudo systemctl enable nginx

# 3. 创建目录结构
sudo mkdir -p /opt/xiyu-bid/{incoming,shared/backend,releases,db-backups,bin}
sudo mkdir -p /srv/www/xiyu-bid
sudo mkdir -p /etc/xiyu-bid
sudo chown -R jetty:jetty /opt/xiyu-bid
sudo chown -R nginx:nginx /srv/www/xiyu-bid

# 4. 配置 Nginx（将前端请求代理到后端 18080）
# 注意：必须包含 gzip + /assets/ 强缓存（2026-08-17 P0 性能优化，缺失会导致页面切换全量重传 JS）
sudo tee /etc/nginx/conf.d/xiyu-bid.conf << 'NGINXEOF'
server {
    listen 80;
    listen 8080;
    server_name _;
    root /srv/www/xiyu-bid;
    index index.html;
    client_max_body_size 3g;

    # gzip 压缩（无此项 vendor 960KB 全量传输，开启后 ~300KB）
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 5;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;

    # index.html 不缓存，保证部署后立即拿到新入口
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
    }

    # hash 化静态资源强缓存 1 年（文件名含 hash，内容不可变）
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable" always;
    }

    # 无 hash 文件名的静态文件不缓存
    location = /favicon.ico { expires -1; add_header Cache-Control "no-cache, no-store, must-revalidate"; }

    # SPA fallback（回退 index.html，随其 no-cache 语义）
    location / {
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:18080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    location /actuator/ {
        proxy_pass http://127.0.0.1:18080/actuator/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
NGINXEOF
sudo nginx -t && sudo systemctl reload nginx
# ⚠️ 禁止添加全局 `location ~* \.(js|css)$ { no-cache }` 之类的 TEMP 块：
#    正则 location 优先级高于 /assets/ 前缀块，会导致 hash 资源强缓存失效（2026-08-17 修复的历史事故）

# 5. 创建 backend.env 模板（实际值需从生产环境获取）
sudo tee /etc/xiyu-bid/backend.env << 'ENVEOF'
# 生产环境变量 — 请替换为实际值
DB_ENGINE=mysql
SPRING_PROFILES_ACTIVE=prod,mysql
SERVER_PORT=18080
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=xiyu_bid_main
DB_USERNAME=root
DB_PASSWORD=<请替换为生产数据库密码>
JWT_SECRET=<请替换为至少32字符的密钥>
CORS_ALLOWED_ORIGINS=<请替换为生产前端域名>
ENVEOF
sudo chmod 600 /etc/xiyu-bid/backend.env

# 6. 创建 systemd 服务
sudo tee /etc/systemd/system/xiyu-bid-backend.service << 'SVCEEOF'
[Unit]
Description=XiYu Bid Backend Service
After=network.target

[Service]
Type=simple
User=jetty
WorkingDirectory=/opt/xiyu-bid
EnvironmentFile=/etc/xiyu-bid/backend.env
ExecStart=/usr/bin/java -jar /opt/xiyu-bid/shared/backend/app.jar
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEEOF
sudo systemctl daemon-reload

# 7. 配置 jetty 用户 sudo 权限（NOPASSWD for systemctl）
echo "jetty ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart xiyu-bid-backend, /usr/bin/systemctl stop xiyu-bid-backend, /usr/bin/systemctl start xiyu-bid-backend, /usr/bin/systemctl status xiyu-bid-backend, /usr/bin/systemctl reload nginx, /usr/bin/chown -R jetty:jetty /srv/www/xiyu-bid" | sudo tee /etc/sudoers.d/xiyu-bid-jetty
sudo chmod 440 /etc/sudoers.d/xiyu-bid-jetty
```

初始化完成后，可以执行首次部署（参考下方 Workflow）。

## Workflow

1. **环境门禁（Step 0 — 硬门禁，不可跳过）**.
   - 按上方"环境选择"章节执行门禁流程
   - 用户未声明 ENV → AI 必须用 AskUserQuestion 询问
   - 用户未确认 → AI 拒绝所有部署操作
   - 确认后设置 `TARGET_HOST`（test=`172.16.38.78`, prod=`172.16.10.149`）

2. **Establish the target environment.**
   - Confirm repository/worktree path, branch, commit, target host, public web URL, API URL, backend service name, app root, frontend public dir, and database name.
   - Say clearly whether you are preparing a plan, editing release automation, executing a deployment, or diagnosing a failed deployment.

3. **早操三连（每个部署任务必做）**.
   ```bash
   source scripts/dev-env.sh
   bash scripts/sync-env.sh .
   bash scripts/check-git-wrapper.sh
   ```
   - 锚点分支 `agent/trae-init` 上执行 `sync-env.sh` 是 ff-only 同步，不是开发行为
   - 确认 `git status --short` 干净，HEAD = origin/main
   - 确认 GitHub 镜像同步状态：`git log --oneline github/main..origin/main | wc -l`（应为 0）

4. **Inspect the current release surface.**
   - Read project docs and scripts before acting: `docs/release/PRODUCTION_RELEASE_PIPELINE.md`, `docs/release/GO_LIVE_CHECKLIST.md`, `docs/release/ROLLBACK.md`, `scripts/release/*`.
   - 查询服务器当前部署：`ssh jetty@${TARGET_HOST} 'cat /opt/xiyu-bid/deployed-release.json'`
   - 健康检查（经 Nginx 代理，外部访问）：`curl --noproxy '*' -s http://${TARGET_HOST}:8080/actuator/health`
   - 或直接检查后端（需在服务器本地执行）：`curl -s http://127.0.0.1:18080/actuator/health`
   - 检查增量 commit 和 Flyway 迁移文件变更：
     ```bash
     git log --oneline <prev-commit>..HEAD
     git diff --name-only <prev-commit>..HEAD -- backend/src/main/resources/db/migration-mysql/
     ```

5. **Verify release readiness（Flyway 预检 3 步法 + 打包校验）**.
   - **Step 1**: 服务器跑 `bash /opt/xiyu-bid/bin/flyway-repair-runner.sh validate`（确认 DB 当前状态健康）
   - **Step 2**: 对比 DB 已应用版本 vs 源码最新版本（服务器 `/tmp/migration-mysql/` 可能过时，直接查 SQL）：
     ```bash
     ssh jetty@${TARGET_HOST} 'source /etc/xiyu-bid/backend.env && mysql -h"${DB_HOST:-127.0.0.1}" -P"${DB_PORT:-3306}" -u"${DB_USER:-root}" -p"${DB_PASSWORD}" "${DB_NAME:-xiyu_bid_main}" -e "SELECT version, description, success, installed_on FROM flyway_schema_history WHERE type=\"SQL\" AND success=1 ORDER BY installed_rank DESC LIMIT 5;"'
     ```
   - **Step 3**: `remote-deploy.sh` 会在激活新 jar 前自动跑 validate（失败则停止 rollout，旧 jar 仍在运行）
   - 本地打包前确认 `mvn clean -DskipTests package`（强制 clean，避免脏 target）
   - 打包后校验 jar 内迁移文件无重复版本：
     ```bash
     unzip -l .release/<release-id>/backend/app.jar 'BOOT-INF/classes/db/migration-mysql/V*.sql' | tail -5
     ```
   - Before production execution, require backup and rollback anchors: release tag or commit, previous frontend artifact, previous backend artifact, database backup, environment snapshot, and rollback owner.

6. **Execute deployment safely（标准打包 + 部署）**.
   - **本地打包**（生产同源构建模式 + OBS 直传启用）：
     ```bash
     RELEASE_ID="<commit>" VITE_API_BASE_URL= VITE_OBS_ENABLED=true COPYFILE_DISABLE=1 bash scripts/release/package-release.sh
     ```
     - **关键**：`VITE_API_BASE_URL=` 显式设空，触发 `src/api/config.js` 的同源构建（`baseURL=""`）
     - **关键**：`VITE_OBS_ENABLED=true` 显式启用 OBS 大文件直传（自第 8 次生产事故后脚本默认已改为 true，但生产部署仍显式传入作双保险）
     - **关键**：`COPYFILE_DISABLE=1` 避免 macOS `._*` 残留文件污染服务器
     - 历史 release ID 后缀 `-api8080` 仅为命名习惯，不代表后端端口。当前后端内部端口统一为 `18080`
     - 不要 grep 构建产物 JS 找目标 IP —— 同源构建里根本没有 IP 字面量
     - 验证 `check:frontend-api-base` 步骤通过即可
     - **产物校验（必做）**：打包后必须验证 OBS 直传已启用：
       ```bash
       # 检查 release-metadata.json 中 obsEnabled=true
       cat .release/<release-id>/release-metadata.json | grep obsEnabled
       # 检查 Detail chunk 中 .upload( 调用数 >=2（OBS 直传逻辑未被 tree-shake）
       grep -o "\\.upload(" .release/<release-id>/frontend/assets/Detail-*.js | wc -l
       ```
   - **上传 + 部署**：
     ```bash
     scp .release/xiyu-bid-release-<release-id>.tar.gz scripts/release/remote-deploy.sh jetty@${TARGET_HOST}:/opt/xiyu-bid/incoming/

     ssh jetty@${TARGET_HOST} 'set -e; cd /opt/xiyu-bid/incoming && \
       source /etc/xiyu-bid/backend.env && \
       RELEASE_ARCHIVE=/opt/xiyu-bid/incoming/xiyu-bid-release-<release-id>.tar.gz \
       APP_ROOT=/opt/xiyu-bid \
       FRONTEND_PUBLIC_DIR=/srv/www/xiyu-bid \
       BACKEND_SERVICE_NAME=xiyu-bid-backend \
       HEALTHCHECK_URL=http://127.0.0.1:18080/actuator/health \
       RELEASE_ID=<release-id> \
       FLYWAY_REPAIR_RUNNER=/opt/xiyu-bid/bin/flyway-repair-runner.sh \
       SYSTEMCTL_SUDO=true \
       DB_BACKUP_COMMAND="source /etc/xiyu-bid/backend.env && mysqldump -h\"\${DB_HOST:-127.0.0.1}\" -P\"\${DB_PORT:-3306}\" -u\"\${DB_USER:-root}\" -p\"\${DB_PASSWORD}\" \"\${DB_NAME:-xiyu_bid_main}\" | gzip > /opt/xiyu-bid/db-backups/winbid-<release-id>-\$(date +%Y%m%d%H%M%S).sql.gz && echo DB backup done" \
       bash /opt/xiyu-bid/incoming/remote-deploy.sh'
     ```
   - **关键**：`SYSTEMCTL_SUDO=true` 让 remote-deploy.sh 用 sudo 重启服务（jetty 用户已配置 NOPASSWD sudo）。否则会因 `Interactive authentication required` 失败，jar 已覆盖但服务未重启。
   - Keep production secrets out of chat, logs, docs, and committed files.
   - **前端资源保留（防止跨版本 404）**：`remote-deploy.sh` 覆盖 `/srv/www/xiyu-bid` 时会删除旧 hash 化静态资源。若用户浏览器仍有未刷新的旧标签页，其 `<link rel="preload">` 指向已删除的旧 CSS/JS → Nginx 404 → Sentry 噪声。部署后应执行：
     ```bash
     # 保留上一版本 assets 目录 24h，让旧标签页有机会自然刷新
     ssh jetty@${TARGET_HOST} 'PREV=$(cat /opt/xiyu-bid/deployed-release.json | grep -o "\"releaseDir\":\"[^\"]*\"" | cut -d"\"" -f4) && \
       if [ -n "$PREV" ] && [ -d "$PREV/frontend" ]; then \
         sudo cp -rn "$PREV/frontend/assets/"* /srv/www/xiyu-bid/assets/ 2>/dev/null; \
         echo "✅ 已保留上一版本 assets"; \
       fi'
     ```

7. **Prove the deployment（健康检查 + Smoke）**.
   - 后端重启后等待健康检查（最多 4 分钟，Kafka SDK 启动延迟属正常）：
     ```bash
     ssh jetty@${TARGET_HOST} 'for i in $(seq 1 120); do if curl -fsS http://127.0.0.1:18080/actuator/health >/dev/null 2>&1; then echo "✅ 健康检查通过 (第 ${i} 次)"; break; fi; sleep 2; done'
     ```
   - 验证 Flyway 迁移已应用：
     ```bash
     ssh jetty@${TARGET_HOST} 'source /etc/xiyu-bid/backend.env && mysql -h"${DB_HOST:-127.0.0.1}" -P"${DB_PORT:-3306}" -u"${DB_USER:-root}" -p"${DB_PASSWORD}" "${DB_NAME:-xiyu_bid_main}" -e "SELECT version, description, success, installed_on FROM flyway_schema_history WHERE version IN (<new-versions>) ORDER BY version;"'
     ```
   - API Smoke（admin 密码未知时用 400/403/401 验证接口路由；以下均经 Nginx `8080` 代理到后端 `18080`）：
     ```bash
     curl --noproxy '*' -s -o /dev/null -w "HTTP %{http_code}\n" http://${TARGET_HOST}:8080/actuator/health              # 200 UP
     curl --noproxy '*' -s -o /dev/null -w "HTTP %{http_code}\n" http://${TARGET_HOST}:8080/actuator/health/readiness    # 200 UP
     curl --noproxy '*' -s -X POST -H "Content-Type: application/json" -d '{}' http://${TARGET_HOST}:8080/api/auth/login  # 400 (空密码验证错误)
     curl --noproxy '*' -s -o /dev/null -w "HTTP %{http_code}\n" http://${TARGET_HOST}:8080/api/projects                 # 403 (需认证)
     curl --noproxy '*' -s -o /dev/null -w "HTTP %{http_code}\n" http://${TARGET_HOST}:8080/api/integration/crm/health   # 401 (需认证)
     ```
   - 前端验证（经 Nginx `8080`）：
     ```bash
     curl --noproxy '*' -s -o /dev/null -w "HTTP %{http_code}\n" http://${TARGET_HOST}:8080/        # 200
     curl --noproxy '*' -s -o /dev/null -w "HTTP %{http_code}\n" http://${TARGET_HOST}:8080/login   # 200
     curl --noproxy '*' -s http://${TARGET_HOST}:8080/ | grep -oE 'assets/index-[A-Za-z0-9_-]+\.js'  # 与 release 一致
     ```
   - GitHub 镜像同步检查（如落后则 `bash scripts/sync-to-github.sh`）
   - Capture exact commit, release id, URLs checked, smoke result, and any skipped checks with reasons.

8. **Generate deployment report（部署报告纪律）**.
   - **每次部署必须生成报告**，即使代码变更小（第 12 次部署报告缺失是反面教材）
   - 报告路径：`docs/release/deploy-report-YYYY-MM-DD-Nth.md`
   - 报告必须包含：部署环境（test/prod）、部署概览、基线信息、PR 列表、改动范围、Flyway 预检结果、部署步骤、验证结果、GitHub 同步、回滚信息、经验沉淀应用情况、风险提示、部署确认清单
   - 报告生成后建议提 PR 合入 main（PR 标题示例：`docs(release): 第 N 次部署报告 (test/prod)`）

9. **Handle failure decisively.**
   - If health or P0 smoke fails, stop forward rollout.
   - Prefer rollback to the previous known-good artifact when the issue blocks core login, API health, project/tender access, or cannot be fixed within the maintenance window.
   - Never run destructive database recovery commands unless the user explicitly confirms the target database and backup.

## Response Shape

When reporting results, include:

- Environment (test/prod) and release id/commit.
- Commands or workflows run.
- Verification result, including health and smoke.
- Rollback posture: ready, not needed, executed, or blocked.
- Files changed, if any.

## Standard Deployment SOP（双环境版）

完整的标准化部署流程，从早操到报告：

```
 0. 环境门禁          → 用户声明 ENV=test|prod + AI 展示确认信息 + AskUserQuestion 确认
 1. 早操三连          → source dev-env.sh + sync-env.sh + check-git-wrapper.sh
 2. 确认基线          → git status + git log + git diff origin/main + GitHub 同步检查
 3. 服务器现状        → deployed-release.json + health + 增量 commit + 迁移文件变更
 4. Flyway 预检 3 步  → validate + DB 版本对比 + remote-deploy 内置
 5. 本地打包          → RELEASE_ID + VITE_API_BASE_URL= + VITE_OBS_ENABLED=true + COPYFILE_DISABLE=1 + package-release.sh
 6. 产物校验          → jar 内迁移文件数 + V*.sql 无重复 + 前端 index.html 入口 + **OBS obsEnabled=true**
 7. 上传 + 部署        → scp archive + remote-deploy.sh（SYSTEMCTL_SUDO=true）
 7.5 前端资源保留     → 从上一版本 release 目录 cp -rn 旧 assets 到 /srv/www/xiyu-bid/assets/
 8. 健康检查          → 等待 UP（最多 4 分钟，容忍 Kafka 延迟）
 9. 迁移应用验证      → SQL 查询 flyway_schema_history
10. Smoke 测试       → health + readiness + 3 个接口路由 + 前端页面
11. GitHub 镜像同步  → 检查 + 必要时 sync-to-github.sh
12. 配置清理检查     → SHOW_DETAILS/DEBUG/TRACE 临时配置
13. 部署报告         → docs/release/deploy-report-YYYY-MM-DD-Nth.md（标注环境）
```

## Key Lessons from Deployment Practice (15 次部署实战沉淀)

以下 18 条经验从第 3-35 次测试环境部署实战中沉淀。部署前必读，避免重复踩坑。

### 1. Flyway 预检 3 步法（避免启动失败）

不要只等后端启动时才发现 Flyway 问题——部署前主动执行 3 步验证：

```bash
# Step 1: 服务器跑 validate（确认 DB 当前状态健康）
ssh jetty@${TARGET_HOST} 'bash /opt/xiyu-bid/bin/flyway-repair-runner.sh validate'

# Step 2: DB 已应用版本 vs 源码最新版本对比（直接查 SQL，不依赖 /tmp/migration-mysql/）
ssh jetty@${TARGET_HOST} 'source /etc/xiyu-bid/backend.env && mysql ... -e "SELECT version, description, success, installed_on FROM flyway_schema_history WHERE type=\"SQL\" AND success=1 ORDER BY installed_rank DESC LIMIT 5;"'

# Step 3: remote-deploy.sh 会在激活新 jar 前自动跑 validate
# 失败则停止 rollout，旧 jar 仍在运行
```

**关键发现（Flyway 9.22.3）**：
- `flyway_schema_history` 中**手动 INSERT 的记录**如果 `checksum=NULL`，validate **不算 mismatch**（跳过 checksum 验证）。这降低了手动 Flyway 修复的风险——但仍应优先用 `flyway-repair-runner.sh repair` 走正规流程，手动 INSERT 仅作最后兜底。
- **查询 flyway_schema_history 必须加 `success=1` 过滤**（第 6 次 V1039 事故根因：未过滤 failed 记录导致误判）
- `flyway-repair-runner.sh` 在服务器 `/opt/xiyu-bid/bin/`，不在 `scripts/release/`

### 2. Readiness 延迟恢复（Kafka SDK 时序竞争）

如果后端重启后 `/actuator/health/readiness` 返回 503 OUT_OF_SERVICE：

- **根因**：`OrganizationEventSdkKafkaStarter` 使用 `@EventListener(ApplicationReadyEvent.class) @Order(LOWEST_PRECEDENCE)`。若 Kafka 初始化阻塞主线程（网络超时），会延迟 `AvailabilityChangeEvent` 处理，导致 readiness 长时间停留在 OUT_OF_SERVICE。
- **现象**：后端其他组件显示 UP，但 readiness 持续 503 达 2-5 分钟（第 8 次 4 分钟，第 15 次 2 分 36 秒）。
- **恢复**：Kafka broker 可达后通常自恢复，不必急于回滚。
- **修复方向**：考虑将 `OrganizationEventSdkKafkaStarter.onApplicationReady()` 改为 `@Async` 或独立线程池执行，避免阻塞主线程。
- **历史出现**：第 8、9、10、13、15 次均出现，已沉淀为已知行为。

### 3. 生产前端同源构建（baseURL=""）

生产构建时 `src/api/config.js` 在 `import.meta.env.PROD=true` 时**强制 `baseURL=""`（同源）**：

```js
// src/api/config.js:47
export const API_BASE_URL = import.meta.env.PROD ? '' : normalizeApiBaseUrl(viteEnv.VITE_API_BASE_URL)
```

会忽略 `VITE_API_BASE_URL`。这是设计——前端+后端同入口经 nginx 反代，同源是唯一"无论从哪个 origin 访问都不跨域"的方案。

**正确的打包命令**：
```bash
RELEASE_ID="<commit>" VITE_API_BASE_URL= bash scripts/release/package-release.sh
```

> 历史 release ID 后缀 `-api8080` 仅为命名习惯，不代表后端端口。当前后端内部端口统一为 `18080`。

### 4. Smoke 测试限制（Admin 密码未知）

如果 `ADMIN_PASSWORD` 环境变量未知，完整登录 smoke 无法完成。**替代验证方案**（以下均经 Nginx `8080` 代理到后端 `18080`）：

```bash
curl --noproxy '*' -s http://${TARGET_HOST}:8080/actuator/health
curl --noproxy '*' -s -X POST -H "Content-Type: application/json" -d '{}' http://${TARGET_HOST}:8080/api/auth/login
curl --noproxy '*' -s http://${TARGET_HOST}:8080/api/projects
curl --noproxy '*' -s http://${TARGET_HOST}:8080/api/integration/crm/health
```

### 5. GitHub 镜像同步

部署到 Gitee main 后，GitHub 镜像可能落后：

```bash
git log --oneline github/main..origin/main | wc -l
bash scripts/sync-to-github.sh
```

> 仅主工作区（`/Users/user/xiyu/worktrees/trae`）执行同步，其他 worktree 不推镜像。

### 6. 临时调试配置清理

排障期间可能往 `/etc/xiyu-bid/backend.env` 添加了临时配置，部署完成后**必须检查**：

```bash
ssh jetty@${TARGET_HOST} 'sudo grep -E "SHOW_DETAILS|DEBUG|TRACE" /etc/xiyu-bid/backend.env'
```

### 7. 幂等迁移设计（部署安全底线）

所有新迁移**尽量幂等**，防止重复执行/部分执行后产生冲突。

**Flyway 9.22.3 + MySQL 8.0 语法限制**：
- ❌ `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` —— Flyway 9.22.3 会记录为 `success=0`（第 4 次 V1101 事故）
- ✅ 存储过程 + `information_schema` 检查（复杂场景）
- ✅ `UPDATE ... WHERE NOT LIKE` 检查（追加权限类操作）

### 8. systemctl sudo 权限（第 15 次发现，PR !1324 已修复）

`remote-deploy.sh` 默认 `SYSTEMCTL_SUDO=true`（PR !1324 后调整，原默认 `false` 导致第 15 次部署事故）。

### 9. git.properties commit id 不准确（第 11 次发现）

worktree `.git` 指向问题导致 `git.properties` 中 `git.commit.id` 显示旧 commit。

### 10. 破坏性 schema 变更（DROP COLUMN）（第 15 次 V1108）

破坏性 DROP+ADD 迁移需特别关注：数据无法回滚恢复，需从 DB 备份恢复整张表。

### 11. 服务器 /tmp/migration-mysql/ 目录过时（第 15 次发现）

不影响 validate，但建议部署时同步更新该目录到最新版本。

### 12. rollback 脚本命名规范（第 15 次误判教训）

新迁移必须配套 rollback 脚本，命名前缀是 `U<version>`（不是 `RV<version>`）。

### 13. 前端目录权限（第 10 次发现）

`/srv/www/xiyu-bid/` 目录属于 `nginx:nginx`，jetty 用户无权删除。解决方案：`sudo chown -R jetty:jetty /srv/www/xiyu-bid/`。

### 14. macOS `._*` 残留文件（第 10 次发现）

从 macOS 打包并 scp 到 Linux 服务器时，会生成 `._*` 元数据残留文件。清理：`find /srv/www/xiyu-bid/ -name "._*" -delete`。预防：打包时设置 `COPYFILE_DISABLE=1`。

### 15. Flyway 防护体系总览（第 10 次事故后建立）

15 项防护覆盖 4 个阶段（截至 2026-06-29）：

| 阶段 | 防护项 | 防护内容 |
|---|---|---|
| pre-commit (7) | 目录守卫 | 拦截 V*.sql/B*.sql 放在 `db/migration/`（历史目录） |
| pre-commit | 配置守卫 | 拦截 `application*.yml` 中 4 个 Flyway 关键配置项修改 |
| pre-commit | 语法守卫 | 拦截 5 种 MariaDB 扩展语法 |
| pre-commit | 回滚脚本 | 检查新迁移是否有对应 rollback 脚本 |
| pre-commit | 已发布不可变 | 拦截修改/重命名 origin/main 已存在的 V*.sql |
| pre-commit | 版本冲突 | 拦截新增 V*.sql 撞号 |
| pre-commit | 逃生阀追踪 | 记录 `FLYWAY_ALLOW_*` / `SKIP_FLYWAY_VALIDATE` 使用 |
| pre-push (4) | DB 同步检查 | 检查"DB 已执行但源码缺失"的迁移 |
| pre-push | 架构测试 | ArchitectureTest / FPJavaArchitectureTest |
| pre-push | 锁检查 | agent:lock-check:changed |
| pre-push | 行预算 | check:line-budgets |
| package-release (2) | 强制 clean | `mvn clean -DskipTests package` |
| package-release | JAR 内重复版本校验 | 打包后 unzip -l 检查无重复 V*.sql |
| remote-deploy (2) | Flyway validate 预检 | 覆盖 jar 前无条件 validate |
| remote-deploy | 健康检查 | 重启后等待 health UP（最多 4 分钟） |

**防复发效果**：第 11-15 次未再发生 Flyway 启动失败事故。

### 16. Mac HTTP_PROXY 导致外部访问 502（第 19/23 次发现）

本地 Mac 开启了 HTTP 代理（如 Clash/V2Ray 等），导致 `curl http://<内网IP>:8080` 走代理隧道返回 502。

**绕过方式**：
```bash
curl --noproxy '*' http://${TARGET_HOST}:8080/actuator/health
```

- 部署脚本中的 `curl` 命令统一加 `--noproxy '*'`，避免环境变量干扰

### 17. SentryAppender 手动声明导致 crash-loop（第 34 次事故，PR !1519 引入）

`logback-spring.xml` 手动声明 `io.sentry.logback.SentryAppender`，但项目仅引入 `sentry-spring-boot-starter-jakarta`（**不包含 `sentry-logback` 模块**），logback 初始化时找不到该类，后端 crash-loop 约 10 分钟。

**修复方式**（PR !1533）：移除 `logback-spring.xml` 中 `SentryAppender` 手动声明。Spring Boot Starter 会**自动配置** SentryAppender，**不需要**在 logback.xml 中手动声明。

### 18. 前端 hash 资源跨版本 404（Unable to preload CSS）

**根因**：前端构建产物使用 hash 化文件名（如 `assets/index-ABC.js`）。`remote-deploy.sh` 发版时直接覆盖 `/srv/www/xiyu-bid`，旧 hash 文件被删除。用户浏览器中仍有未刷新的旧标签页（或缓存的 HTML），其 `<link rel="preload">` 指向已不存在的旧 CSS/JS → Nginx 404 → Vue/Sentry 捕获 `Unable to preload CSS`。

**这不是代码逻辑缺陷**，而是部署生命周期问题：
- 用户侧：旧标签页 / 浏览器缓存的 HTML 引用了旧 hash 资源
- 运维侧：发版时未保留上一版本的静态资源

**解决方案**（优先级从高到低）：

1. **部署时保留旧资源（推荐）**：`remote-deploy.sh` 切换前端目录后，从上一版本 release 目录 `cp -rn` 旧 `assets/*` 到 `/srv/www/xiyu-bid/assets/`，保留 24h 让旧标签页自然刷新：
   ```bash
   ssh jetty@${TARGET_HOST} 'PREV=$(cat /opt/xiyu-bid/deployed-release.json | grep -o "\"releaseDir\":\"[^\"]*\"" | cut -d"\"" -f4) && \
     if [ -n "$PREV" ] && [ -d "$PREV/frontend" ]; then \
       sudo cp -rn "$PREV/frontend/assets/"* /srv/www/xiyu-bid/assets/ 2>/dev/null; \
       echo "✅ 已保留上一版本 assets"; \
     fi'
   ```
   - `cp -rn`：不覆盖已有文件（新版本的 hash 文件优先），只补回被删除的旧 hash 文件
   - 24h 后由定时任务清理过期资源（或下次部署时清理超过 24h 的旧文件）

2. **Nginx 回退策略（不推荐作首选）**：对 `/assets/*` 的 404 回退到 `index.html`。风险：会掩盖真实 404，影响前端资源缺失监控。

3. **前端容错（补充手段）**：对 `<link rel="preload">` 增加 `onerror` 降级处理，避免未处理异常进入 Sentry。只能减少噪声，不能解决资源缺失。

### 19. Nginx TEMP no-cache 块导致页面切换全量重传（2026-08-17 修复）

**根因**：服务器 `/etc/nginx/conf.d/xiyu-bid.conf` 中遗留一段 "TEMP: disable JS/CSS cache for deployment refresh" 的临时配置——`location ~* \.(js|css)$ { no-cache, no-store }`，且全局未开 gzip。两个因素叠加：每次页面切换，所有 hash 化 chunk 全量重新下载（vendor 960KB + echarts 822KB + 页面 chunk），无压缩传输。这是"页面切换内容展示慢"的第一根因（占比远超 API 耗时）。

**Nginx 陷阱**：正则 location（`~*`）优先级高于前缀 location（`/assets/`）。只要存在全局 JS/CSS 正则 no-cache 块，`/assets/` 里配置的强缓存永远不会生效——删掉正则块是强缓存生效的前提。

**修复（双环境已落地，2026-08-17）**：
- 顶层加 `gzip on` + 8 类 MIME（JS/CSS/JSON/SVG 等）
- 删除 TEMP 正则 no-cache 块
- `/assets/`（hash 资源）→ `expires 1y` + `Cache-Control: public, immutable`
- `index.html` 保持 no-cache（保证部署刷新入口）；favicon 等无 hash 文件保持 no-cache

**实测收益**：vendor chunk 传输 960KB → 300KB（gzip，-69%）；二次访问 chunk 命中强缓存零传输。回滚锚点：`/etc/nginx/conf.d/xiyu-bid.conf.bak-20260817`（双环境均保留）。

**验证命令**：
```bash
curl --noproxy '*' -sI -H 'Accept-Encoding: gzip' https://winbid.ehsy.com/assets/<vendor-chunk>.js | grep -iE 'content-encoding|cache-control'
# 期望：Content-Encoding: gzip + Cache-Control: public, immutable
```

**防复发**：skill 初始化模板已含 gzip + 强缓存；禁止再引入全局 JS/CSS no-cache 正则块（部署刷新需求由 index.html no-cache 满足，hash 资源无需 no-cache）。

## 部署历史 commit 链（第 3-35 次，全部为测试环境）

| # | 环境 | 日期 | Release ID | 新增迁移 | 备注 |
|---|---|---|---|---|---|
| 3 | test | 2026-06-26 | `e51a673bc` | 无 | CO-346 CRM 回调 systemName |
| 4 | test | 2026-06-26 | `b1f62bfab` | 无 | V1099→V1101 重命名失败后删除（Flyway 语法事故） |
| 5 | test | 2026-06-26 | `8f5497693` | 无 | 补回 V1100 源码 |
| 6 | test | 2026-06-26 | `8ed1ac7dd` | V1102 | V1039 failed migration 事故（最严重） |
| 7 | test | 2026-06-27 | `0571e25b` | V1103 | V1103 NULL checksum 容忍性发现 |
| 8 | test | 2026-06-27 | `3bb444139` | V1104, V1105 | Kafka SDK readiness 4 分钟延迟 |
| 9 | test | 2026-06-27 | `47a0e2bba` | 无 | readiness 延迟已沉淀为已知行为 |
| 10 | test | 2026-06-28 | `92b7dadb` | V1106（热修复） | V1106 放错目录导致 30 分钟生产中断（最大事故） |
| 11 | test | 2026-06-28 | `e261db3bd` | 无 | flyway repair 对齐 V1103/V1106 NULL checksum |
| 12 | test | 2026-06-28 | `dfe1d828` | 无 | **报告缺失**（第 13 次补记） |
| 13 | test | 2026-06-28 | `c577dec2c` | 无 | 7 条关键经验正式沉淀 |
| 14 | test | 2026-06-29 | `cb6796cef` | V1107 | ExternalUrlGuard 测试 |
| 15 | test | 2026-06-29 | `05656257e` | V1108, V1109 | CO-393 项目负责人视图权限，systemctl sudo 问题发现 |
| 16 | test | 2026-06-30 | `1c23e53a7` | 无 | SidecarHealthIndicator GET 请求修复 |
| 17 | test | 2026-06-30 | `8626f0e20` | 无 | MarkItDownSidecarExtractor root cause + 测试补全 |
| 18 | test | 2026-06-30 | `bd7eedfaf` | 无 | Sentry SDK 集成，DSN 配置，环境标识 |
| 19 | test | 2026-06-30 | `b59aafa80` | 无 | 第 19 次部署报告，Mac HTTP_PROXY 502 首次发现 |
| 20 | test | 2026-06-30 | `2f68c19db` | 无 | 统一 Sidecar 配置 key，AI service retry |
| 21 | test | 2026-06-30 | `326869f88` | V1119, V1120 | CO-406 AI 抽取标讯原文 |
| 22 | test | 2026-06-30 | `b728ee241` | V1121, V1122, V1123 | CO-394 权限注解迁移 |
| 23 | test | 2026-06-30 | `c32d80aba` | V1121, V1122, V1123 | CO-394 系列整改 |
| 24 | test | 2026-07-01 | `261830696` | 无 | 第 25 次部署：CO-430/431/432/435/436/437/438 系列 |
| 25 | test | 2026-07-01 | `261830696-api8080` | 无 | PR !1425-!1435 增量部署 |
| 26-29 | test | 2026-07-01 | （略） | 无 | 第 26-29 次部署（中间部署） |
| 30 | test | 2026-07-01 | `b962dc953-api8080` | 无 | PR !1480-!1490 增量部署，CO-447 列表排序 |
| 31-33 | test | 2026-07-02 | （略） | 无 | 第 31-33 次部署（中间部署） |
| 34 | test | 2026-07-02 | `0f026a9b7-api8080` | 无 | ❌ P0 事故：SentryAppender crash-loop（PR !1519），已回滚 |
| 35 | test | 2026-07-02 | `0a057f757-api8080` | 无 | ✅ Sentry P0 修复（PR !1533）上线 |

## 反复出现的问题清单

> 以下问题在 3 次以上部署中出现，需特别关注：

1. **Flyway 迁移治理**（7 次故障）：版本号重复、源码缺失、放错目录、MariaDB 语法、checksum mismatch、NULL checksum — 第 3、4、5、6、7、10、11 次
2. **Kafka SDK readiness 延迟**（5 次出现）：第 8、9、10、13、15 次 — 已沉淀为已知行为
3. **Smoke 测试 admin 密码限制**（9 次跳过）：第 6-15 次 — 用 400/403/401 替代验证
4. **SHOW_DETAILS=always 保留**（3 次决定保留）：第 13、14、15 次 — 用户决定
5. **rollback 脚本缺失**（3 次缺失）：V1107、V1108、V1109 — 需补全
6. **GitHub 镜像同步**（3 次明确处理）：第 3 次发现落后，第 8 次明确待办，第 13 次起作为标准步骤
7. **Mac HTTP_PROXY 502**（2 次出现）：第 19 次首次发现，第 23 次复发——绕过代理后正常，属 Mac 代理问题非服务故障
8. **SentryAppender crash-loop**（1 次事故）：第 34 次首次发现，logback.xml 手动声明 SentryAppender 但未引入 sentry-logback 依赖
9. **前端 hash 资源跨版本 404**（部署生命周期问题）：发版直接覆盖 `/srv/www/xiyu-bid` 删除旧 hash 文件，旧标签页 `<link rel="preload">` 指向已删除资源 → Nginx 404 → Sentry 噪声。解决方案：部署后从上一版本 release 目录 `cp -rn` 旧 assets 保留 24h
10. **OBS 直传漏传 VITE_OBS_ENABLED=true**（2 次事故）：第 84 次测试 + 第 8 次生产均漏传，导致 `isObsEnabled` 编译为 `!1`（false），OBS 大文件直传失效。**根治修复**：`package-release.sh` 默认值已从 `false` 改为 `true`（不传也启用），skill 打包模板已显式传入 `VITE_OBS_ENABLED=true` 作双保险，产物校验加 `obsEnabled` 检查