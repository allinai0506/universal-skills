# XiYu Release Runbook

> 本文档基于第 3-35 次生产部署实战经验（2026-06-26 至 2026-07-02）沉淀。
> 最后更新：2026-07-09（双环境改造）

## Project Documents To Read

In a XiYu worktree, start with these files when present:

- `docs/release/PRODUCTION_RELEASE_PIPELINE.md`
- `docs/release/GO_LIVE_CHECKLIST.md`
- `docs/release/ROLLBACK.md`
- `docs/release/ROLLBACK_RUNBOOK.md`
- `docs/release/PERFORMANCE_SECURITY_BACKUP_MONITORING_DELIVERY.md`
- `.wiki/pages/deployment.md`
- `.github/workflows/main-release.yml`
- `scripts/release/package-release.sh`
- `scripts/release/remote-deploy.sh`
- `scripts/release/preflight.sh`
- `scripts/release/run-prod-smoke.mjs`

## Environment Selection (Hard Gate)

> **部署前必须通过环境门禁。** 详细流程见 `SKILL.md § 环境选择（硬门禁）`。

| 环境 | ENV 值 | IP | TARGET_HOST | 用途 |
|------|--------|-----|-------------|------|
| 测试 | `test` | `172.16.38.78` | `172.16.38.78` | 日常部署验证 |
| 生产 | `prod` | `172.16.10.149` | `172.16.10.149` | 正式环境 |

以下所有命令中的 `${TARGET_HOST}` 在 test 环境替换为 `172.16.38.78`，在 prod 环境替换为 `172.16.10.149`。

## Known Winbid Servers

### Test Server (winbid-01.test)

- Host: `172.16.38.78`
- SSH user: `jetty`
- Direct access probe: `ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 jetty@172.16.38.78 'hostname; date; whoami'`
- App root: `/opt/xiyu-bid`
- Incoming artifacts: `/opt/xiyu-bid/incoming/`
- Backend runtime jar: `/opt/xiyu-bid/shared/backend/app.jar`
- Backend service: `xiyu-bid-backend`
- **Backend port: `8080`（不是 18080）**
- Frontend public dir: `/srv/www/xiyu-bid/`（所有权 `nginx:nginx`）
- Backend env file: `/etc/xiyu-bid/backend.env`（`sudo` required to read）
- Flyway repair runner: `/opt/xiyu-bid/bin/flyway-repair-runner.sh`
- DB backups: `/opt/xiyu-bid/db-backups/`
- Deployed record: `/opt/xiyu-bid/deployed-release.json`
- MySQL: `winbid-01.test.rds.ehsy.com:3306`, database `winbid`, user `ea_bid`
- Redis: `winbid-01.test.redis.ehsy.com:6379`
- 部署历史: 35 次

### Prod Server (winbid-01.prod)

- Host: `172.16.10.149`
- SSH user: `jetty`
- Direct access probe: `ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 jetty@172.16.10.149 'hostname; date; whoami'`
- 当前状态: 空机器，需初始化（Java 1.8 → 升级到 21，无 Nginx，无目录结构）
- 初始化步骤: 见 `SKILL.md § 生产环境首次初始化`
- 部署历史: 0 次（待首次部署）

### 双环境通用配置

| 项目 | 值 |
|---|---|
| App root | `/opt/xiyu-bid` |
| Backend service | `xiyu-bid-backend` |
| Backend port | `8080` |
| Frontend public dir | `/srv/www/xiyu-bid/` |
| Backend env file | `/etc/xiyu-bid/backend.env` |
| Flyway repair runner | `/opt/xiyu-bid/bin/flyway-repair-runner.sh` |
| DB backups | `/opt/xiyu-bid/db-backups/` |
| Deployed record | `/opt/xiyu-bid/deployed-release.json` |

Never record the smoke account password, DB password, Redis password, private key, or copied `backend.env` contents in docs, skill files, chat, or committed files.

## Production Configuration

Backend production profile baseline:
```bash
export DB_ENGINE=mysql
export SPRING_PROFILES_ACTIVE=prod,mysql
export DB_HOST=<mysql-host>
export DB_PORT=3306
export DB_NAME=<database>
export DB_USERNAME=<user>
export DB_PASSWORD=<secret>
export JWT_SECRET=<at-least-32-chars>
export CORS_ALLOWED_ORIGINS=<production-web-origin>
```

## Manual Deployment Skeleton

```bash
# 0. 环境门禁（硬门禁，不可跳过）
# 用户声明 ENV=test|prod，AI 用 AskUserQuestion 确认目标环境

# 1. 早操三连
source scripts/dev-env.sh
bash scripts/sync-env.sh .
bash scripts/check-git-wrapper.sh

# 2. Flyway 预检 Step 1
ssh jetty@${TARGET_HOST} 'bash /opt/xiyu-bid/bin/flyway-repair-runner.sh validate'

# 3. Flyway 预检 Step 2
ssh jetty@${TARGET_HOST} 'source /etc/xiyu-bid/backend.env && mysql -h"${DB_HOST:-127.0.0.1}" -P"${DB_PORT:-3306}" -u"${DB_USER:-root}" -p"${DB_PASSWORD}" "${DB_NAME:-xiyu_bid_main}" -e "SELECT version, description, success, installed_on FROM flyway_schema_history WHERE type=\"SQL\" AND success=1 ORDER BY installed_rank DESC LIMIT 5;"'

# 4. 本地打包（同源构建）
rm -rf backend/target
RELEASE_ID="<commit>-api8080" VITE_API_BASE_URL= bash scripts/release/package-release.sh

# 5. 产物校验
unzip -l .release/<release-id>/backend/app.jar 'BOOT-INF/classes/db/migration-mysql/V*.sql' | tail -5

# 6. 上传 + 部署
scp .release/xiyu-bid-release-<release-id>.tar.gz scripts/release/remote-deploy.sh jetty@${TARGET_HOST}:/opt/xiyu-bid/incoming/

ssh jetty@${TARGET_HOST} 'set -e; cd /opt/xiyu-bid/incoming && \
  source /etc/xiyu-bid/backend.env && \
  RELEASE_ARCHIVE=/opt/xiyu-bid/incoming/xiyu-bid-release-<release-id>.tar.gz \
  APP_ROOT=/opt/xiyu-bid \
  FRONTEND_PUBLIC_DIR=/srv/www/xiyu-bid \
  BACKEND_SERVICE_NAME=xiyu-bid-backend \
  HEALTHCHECK_URL=http://127.0.0.1:8080/actuator/health \
  RELEASE_ID=<release-id> \
  FLYWAY_REPAIR_RUNNER=/opt/xiyu-bid/bin/flyway-repair-runner.sh \
  SYSTEMCTL_SUDO=true \
  DB_BACKUP_COMMAND="source /etc/xiyu-bid/backend.env && mysqldump -h\"\${DB_HOST:-127.0.0.1}\" -P\"\${DB_PORT:-3306}\" -u\"\${DB_USER:-root}\" -p\"\${DB_PASSWORD}\" \"\${DB_NAME:-xiyu_bid_main}\" | gzip > /opt/xiyu-bid/db-backups/winbid-<release-id>-\$(date +%Y%m%d%H%M%S).sql.gz && echo DB backup done" \
  bash /opt/xiyu-bid/incoming/remote-deploy.sh'
```

## Production Smoke

**Admin 密码未知时的替代验证**：
```bash
curl --noproxy '*' -s http://${TARGET_HOST}:8080/actuator/health
curl --noproxy '*' -s -X POST -H "Content-Type: application/json" -d '{}' http://${TARGET_HOST}:8080/api/auth/login
curl --noproxy '*' -s http://${TARGET_HOST}:8080/api/projects
curl --noproxy '*' -s http://${TARGET_HOST}:8080/api/integration/crm/health
```

## Flyway 防护体系

| 阶段 | 防护项 | 防护内容 |
|---|---|---|
| pre-commit (7) | 目录/配置/语法/回滚/不可变/版本冲突/逃生阀 | 拦截各类违规 |
| pre-push (4) | DB同步/架构测试/锁检查/行预算 | 推送前验证 |
| package-release (2) | 强制clean/JAR重复版本校验 | 打包时验证 |
| remote-deploy (2) | Flyway validate预检/健康检查 | 部署时验证 |

## 常见陷阱速查

| 陷阱 | 现象 | 解决方案 | 来源 |
|---|---|---|---|
| VITE_API_BASE_URL 设错 | CORS 错误 | `VITE_API_BASE_URL=`（显式设空） | 第 3 次 |
| 脏 target 打包 | 重复版本号 | `rm -rf backend/target` 后打包 | 2026-05-28 |
| IF NOT EXISTS 语法 | Flyway success=0 | 存储过程 + information_schema | 第 4 次 |
| 未过滤 success=1 | 误判 failed 迁移 | 必须 `WHERE success=1` | 第 6 次 |
| 迁移文件放错目录 | 500 错误 | 放 `db/migration-mysql/` | 第 10 次 |
| SYSTEMCTL_SUDO 未设 | jar 覆盖但服务未重启 | 设为 true（已为默认） | 第 15 次 |
| 前端目录权限 | Permission denied | `chown -R jetty:jetty` | 第 10 次 |
| macOS ._* 残留 | 前端资源 404 | `find -name "._*" -delete` | 第 10 次 |
| HTTP_PROXY 干扰 | 502 | curl 加 `--noproxy '*'` | 第 19 次 |
| 环境搞混 | 部署到错误环境 | 环境门禁 AskUserQuestion | 2026-07-09 |
__tr_native_ec=$?; pwd -P >| '/var/folders/hb/fw83wt2j5psblns41081bgh40000gn/T/trae-agent-toolhost-501/jobs/job-c4e944f84a8143dea490471ed11bfcd2/cwd.txt'; exit "$__tr_native_ec"