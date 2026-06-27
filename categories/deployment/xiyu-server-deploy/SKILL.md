---
name: xiyu-server-deploy
description: XiYu production server deployment workflow for the 西域数智化投标管理平台. Use when preparing, executing, verifying, documenting, or troubleshooting server deployments, production release pipelines, GitHub production environment variables/secrets, MySQL 8.0 prod profile rollout, API-only smoke checks, rollback planning, or post-deploy release reports for this project.
---

# XiYu Server Deploy

## Operating Contract

Treat the 西域数智化投标管理平台 deployment path as real API only:

- Use `VITE_API_MODE=api` and real backend integration for build, smoke, UAT, screenshots, and acceptance.
- Use MySQL 8.0 for production with `SPRING_PROFILES_ACTIVE=prod,mysql` and `DB_ENGINE=mysql`.
- Do not add or depend on mock/demo/local-memory deployment paths.
- Treat deployment as a closed loop: preflight, backup, artifact activation, health check, smoke verification, report, and rollback readiness.

For detailed variables, scripts, and checklists, read `references/release-runbook.md` when the user asks for exact deployment steps, server setup, GitHub Actions configuration, production verification, or rollback commands.

## Workflow

1. Establish the target environment.
   - Confirm repository/worktree path, branch, commit, target host, public web URL, API URL, backend service name, app root, frontend public dir, and database name.
   - To directly verify server access, use: `ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 jetty@172.16.38.78 'hostname; date; whoami'`.
   - Say clearly whether you are preparing a plan, editing release automation, executing a deployment, or diagnosing a failed deployment.

2. Inspect the current release surface.
   - Read project docs and scripts before acting: `docs/release/PRODUCTION_RELEASE_PIPELINE.md`, `docs/release/GO_LIVE_CHECKLIST.md`, `docs/release/ROLLBACK.md`, `.github/workflows/main-release.yml`, and `scripts/release/*`.
   - Check `git status --short` before edits. Do not overwrite unrelated user changes.

3. Verify release readiness.
   - Prefer the project release gates already present in the repo.
   - For code changes, keep the normal project bar: frontend build/tests as relevant, backend tests as relevant, architecture gates for backend changes, and E2E/API smoke for user-facing deployment behavior.
   - For any local manual package, clean stale backend build output before packaging and inspect the jar for duplicate Flyway versions. A dirty `backend/target` once shipped a deleted `V1001` migration into `app.jar` and caused production startup failure.
   - Before production execution, require backup and rollback anchors: release tag or commit, previous frontend artifact, previous backend artifact, database backup, environment snapshot, and rollback owner.

4. Execute deployment safely.
   - Prefer existing automation over ad hoc SSH commands.
   - Package with `scripts/release/package-release.sh`.
   - If packaging locally, run from a clean build state such as `rm -rf backend/target` or use the CI artifact. After packaging, verify `BOOT-INF/classes/db/migration-mysql` inside `backend/app.jar` contains no duplicate migration versions.
   - **Critical: When packaging frontend locally, must export VITE_API_BASE_URL matching the target server's public endpoint (e.g., http://172.16.38.78:8080 for winbid-01.test). The default 127.0.0.1:18080 will cause CORS errors when browser origin differs.** After packaging, verify the frontend JS contains the correct URL:
     ```bash
     rg "<target-host>:<port>" ".release/<release-id>/frontend/assets"/*.js
     # If this returns nothing, the default 127.0.0.1:18080 was used and CORS will break.
     ```
   - Deploy through GitHub production workflow or `scripts/release/remote-deploy.sh` with explicit environment variables.
   - Keep production secrets out of chat, logs, docs, and committed files.

5. Prove the deployment.
   - Check backend health first, then API read endpoints, then frontend page availability.
   - **If CORS errors appear in browser console during smoke test, it means the frontend was built with the wrong VITE_API_BASE_URL. Rebuild with the correct URL and redeploy.**
   - Run the project's production smoke script when available: `node scripts/release/run-prod-smoke.mjs`.
   - Capture exact commit, release id, URLs checked, smoke result, and any skipped checks with reasons.

6. Handle failure decisively.
   - If health or P0 smoke fails, stop forward rollout.
   - Prefer rollback to the previous known-good artifact when the issue blocks core login, API health, project/tender access, or cannot be fixed within the maintenance window.
   - Never run destructive database recovery commands unless the user explicitly confirms the target database and backup.

## Response Shape

When reporting results, include:

- Environment and release id/commit.
- Commands or workflows run.
- Verification result, including health and smoke.
- Rollback posture: ready, not needed, executed, or blocked.
- Files changed, if any.

## Key Lessons from Deployment Practice (2026-06)

以下 7 条是从第 6-8 次生产部署实战中沉淀的关键经验。部署前必读，避免重复踩坑。

### 1. Flyway 预检 3 步法（避免启动失败）

不要只等后端启动时才发现 Flyway 问题——部署前主动执行 3 步验证：

```bash
# Step 1: 用当前生产 jar 跑 validate（确认 DB 当前状态健康）
bash scripts/release/flyway-repair-runner.sh validate

# Step 2: 检查源码/JAR 迁移文件与生产 DB 一致性（发现缺失/漂移）
bash scripts/check-flyway-db-source-sync.sh

# Step 3: remote-deploy.sh 会在激活新 jar 前自动跑 validate
# 失败则停止 rollout，旧 jar 仍在运行
```

**关键发现（Flyway 9.22.3）**：`flyway_schema_history` 中**手动 INSERT 的记录**如果 `checksum=NULL`，validate **不算 mismatch**（跳过 checksum 验证）。这降低了手动 Flyway 修复的风险——但仍应优先用 `flyway-repair-runner.sh repair` 走正规流程，手动 INSERT 仅作最后兜底。

> 脚本路径已核实：`flyway-repair-runner.sh` 在 `scripts/release/`，而 `check-flyway-db-source-sync.sh` 在 `scripts/`（**不带 `release/` 前缀**）。两者均在生产服务器上执行。

### 2. Readiness 延迟恢复（Kafka SDK 时序竞争）

如果后端重启后 `/actuator/health/readiness` 返回 503 OUT_OF_SERVICE：

- **根因**：`OrganizationEventSdkKafkaStarter`（`backend/src/main/java/com/xiyu/bid/integration/organization/infrastructure/sdk/OrganizationEventSdkKafkaStarter.java`）使用 `@EventListener(ApplicationReadyEvent.class) @Order(LOWEST_PRECEDENCE)`。若 Kafka 初始化阻塞主线程（网络超时），会延迟 `AvailabilityChangeEvent` 处理，导致 readiness 长时间停留在 OUT_OF_SERVICE。
- **现象**：后端其他组件显示 UP，但 readiness 持续 503 达 2-5 分钟。
- **恢复**：Kafka broker 可达后通常自恢复，不必急于回滚。
- **修复方向**：考虑将 `OrganizationEventSdkKafkaStarter.onApplicationReady()` 改为 `@Async` 或独立线程池执行，避免阻塞主线程。

**验证命令**：
```bash
curl -s http://127.0.0.1:8080/actuator/health/readiness
```

### 3. 生产前端同源构建（baseURL=""）

生产构建时 `src/api/config.js` 在 `import.meta.env.PROD=true` 时**强制 `baseURL=""`（同源）**：

```js
// src/api/config.js:47
export const API_BASE_URL = import.meta.env.PROD ? '' : normalizeApiBaseUrl(viteEnv.VITE_API_BASE_URL)
```

会忽略 `VITE_API_BASE_URL`。这是设计——前端+后端同入口经 nginx 反代，同源是唯一"无论从哪个 origin 访问都不跨域"的方案。

**正确的验证方式**：
```bash
# 检查 package-release.sh 内部的 check:frontend-api-base 步骤是否通过（package-release.sh:33）
# 不要 grep 构建产物 JS 找目标 IP —— 同源构建里根本没有 IP 字面量
```

> 与 `## Workflow §4` 中"必须 export VITE_API_BASE_URL"的指引冲突时，以本节为准：生产同源构建模式下显式设空（`VITE_API_BASE_URL=`）才是正确做法，`package-release.sh` 已用 `${VITE_API_BASE_URL+x}` 区分"未设"与"显式空"。

### 4. Smoke 测试限制（Admin 密码未知）

如果 `ADMIN_PASSWORD` 环境变量未知，完整登录 smoke 无法完成。**替代验证方案**：

```bash
# health 端点 200
curl -s http://172.16.38.78:8080/actuator/health
# 登录接口返回 401（密码错是预期，说明接口路由正常）
curl -s -X POST http://172.16.38.78:8080/api/auth/login
```

- CRM smoke 可设 `CRM_SMOKE_MODE=skip`（跳过）或 `required`（空商机=NO-GO，用于强校验）。
- 在 smoke 报告中明确标注"登录 smoke 因密码未授予而跳过"，不要谎称已验证。

### 5. GitHub 镜像同步

部署到 Gitee main 后，GitHub 镜像可能落后：

```bash
# Gitee main → GitHub main 单向镜像
bash scripts/sync-to-github.sh
```

部署前检查同步状态：
```bash
git log --oneline github/main..origin/main | wc -l  # 0 表示已同步
```

> 仅主工作区（`/Users/user/xiyu/worktrees/trae`）执行同步，其他 worktree 不推镜像。

### 6. 临时调试配置清理

排障期间可能往 `/etc/xiyu-bid/backend.env` 添加了临时配置，部署完成后**必须清理**：

```bash
# 检查临时调试配置
sudo grep -E "SHOW_DETAILS|DEBUG|TRACE" /etc/xiyu-bid/backend.env

# 常见需要清理的：
# MANAGEMENT_ENDPOINT_HEALTH_SHOW_DETAILS=always → 恢复为 never（生产默认不暴露健康详情）
```

清理后需重启后端生效，并再次验证端点不再泄露详情。

### 7. 幂等迁移设计（部署安全底线）

所有新迁移必须幂等，防止重复执行/部分执行后产生冲突。MySQL 8.0 原生支持 `IF NOT EXISTS`：

```sql
-- 推荐模式 1：IF NOT EXISTS（简单场景，MySQL 8.0 原生支持）
ALTER TABLE personnel ADD COLUMN IF NOT EXISTS birth_date DATE;

-- 推荐模式 2：存储过程 + information_schema 检查（复杂场景/需多语句事务）
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS repair_personnel_schema() BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema=DATABASE() 
      AND table_name='personnel' 
      AND column_name='birth_date'
  ) THEN
    ALTER TABLE personnel ADD COLUMN birth_date DATE;
  END IF;
END$$
DELIMITER ;
CALL repair_personnel_schema();
```

> 配合 `check-flyway-db-source-sync.sh` 在部署前确认迁移文件与 DB 一致；幂等设计让 `repair`/重放更安全。
