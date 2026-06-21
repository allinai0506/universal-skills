# XiYu Release Runbook

## Project Documents To Read

In a XiYu worktree, start with these files when present:

- `docs/release/PRODUCTION_RELEASE_PIPELINE.md`
- `docs/release/GO_LIVE_CHECKLIST.md`
- `docs/release/ROLLBACK.md`
- `docs/release/PERFORMANCE_SECURITY_BACKUP_MONITORING_DELIVERY.md`
- `.wiki/pages/deployment.md`
- `.github/workflows/main-release.yml`
- `scripts/release/package-release.sh`
- `scripts/release/remote-deploy.sh`
- `scripts/release/preflight.sh`
- `scripts/release/run-prod-smoke.mjs`

Use `rg` to find renamed files if a path is missing:

```bash
rg -n "Production Release|Go-Live|remote-deploy|run-prod-smoke|PROD_APP_ROOT|SPRING_PROFILES_ACTIVE|DB_ENGINE" docs scripts .github .wiki
```

## Production Configuration

GitHub `production` environment usually needs these secrets:

- `PROD_SSH_HOST`
- `PROD_SSH_PORT`
- `PROD_SSH_USER`
- `PROD_SSH_KEY`
- `PROD_SMOKE_USERNAME`
- `PROD_SMOKE_PASSWORD`
- `PROD_DB_BACKUP_COMMAND` when remote deploy should trigger a production DB backup

It usually needs these vars:

- `PROD_APP_ROOT`, for example `/opt/xiyu-bid`
- `PROD_FRONTEND_PUBLIC_DIR`, for example `/srv/www/xiyu-bid`
- `PROD_BACKEND_SERVICE_NAME`, for example `xiyu-bid-backend`
- `PRODUCTION_API_BASE_URL`
- `PRODUCTION_WEB_BASE_URL`

Useful optional vars:

- `PROD_RELEASES_DIR`
- `PROD_BACKEND_RUNTIME_DIR`
- `PROD_BACKEND_JAR_PATH`
- `PROD_DEPLOYED_RELEASE_RECORD`
- `PROD_BACKEND_PORT`
- `PROD_HEALTHCHECK_URL`
- `PROD_SYSTEMCTL_SUDO`
- `PROD_POST_DEPLOY_COMMAND`
- `PROD_PROMETHEUS_MODE`

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

Do not write real secret values into repo files, skill files, release docs, or chat.

## Known Winbid Test Server

Use these concrete values when the target is `winbid-01.test` / `172.16.38.78` and the user has authorized direct server work:

- Host: `172.16.38.78`
- SSH user: `jetty`
- Direct access probe: `ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 jetty@172.16.38.78 'hostname; date; whoami'`
- Legacy deploy key path, when present: `/tmp/xiyu-prod-deploy-crm-test`
- App root: `/opt/xiyu-bid`
- Incoming artifacts: `/opt/xiyu-bid/incoming/app.jar.new`, `/opt/xiyu-bid/incoming/frontend-dist.tar.gz`
- Backend runtime jar: `/opt/xiyu-bid/shared/backend/app.jar`
- Backend service: `xiyu-bid-backend`
- Backend port: `18080`
- Frontend public dir: `/srv/www/xiyu-bid/`
- Backend env file: `/etc/xiyu-bid/backend.env` (`sudo` required to read)
- MySQL: `winbid-01.test.rds.ehsy.com:3306`, database `winbid`, user `ea_bid`
- Redis: `winbid-01.test.redis.ehsy.com:6379`
- Browser-facing API base URL for local frontend packaging: `http://172.16.38.78:8080`

Never record the smoke account password, DB password, Redis password, private key, or copied `backend.env` contents in docs, skill files, chat, or committed files.

Useful server-side checks:

```bash
sudo journalctl -u xiyu-bid-backend --since "5 min ago" --no-pager
sudo systemctl status xiyu-bid-backend --no-pager
curl -s http://localhost:18080/actuator/health
```

If login smoke is blocked by test-environment rate limiting, clear only the exact confirmed Redis key with a placeholder password:

```bash
redis-cli -h winbid-01.test.redis.ehsy.com -a '<redis-password>' DEL '<confirmed-rate-limit-key>'
```

If the deployed frontend appears stale, verify the active nginx assets contain the expected build text or API URL:

```bash
strings /srv/www/xiyu-bid/assets/*.js | rg '<expected-code-keyword>|172.16.38.78:8080' -m 3
```

## Manual Deployment Skeleton

Prefer GitHub Actions when configured. For a controlled manual deployment, adapt this shape:

```bash
bash scripts/release/preflight.sh
rm -rf backend/target
PRODUCTION_API_BASE_URL=<browser-facing-api-url> \
VITE_API_BASE_URL=<browser-facing-api-url> \
bash scripts/release/package-release.sh

jar tf .release/<release-id>/backend/app.jar \
  | rg 'BOOT-INF/classes/db/migration-mysql/V[0-9]+__' \
  | sed -E 's#.*\/(V[0-9]+)__.*#\1#' \
  | sort \
  | uniq -d

RELEASE_ARCHIVE=/path/to/release.tar.gz \
APP_ROOT=/opt/xiyu-bid \
FRONTEND_PUBLIC_DIR=/srv/www/xiyu-bid \
BACKEND_SERVICE_NAME=xiyu-bid-backend \
HEALTHCHECK_URL=https://api.example.com/actuator/health \
DB_BACKUP_COMMAND=/opt/xiyu/bin/backup-prod-db.sh \
bash scripts/release/remote-deploy.sh
```

The duplicate-version check must print nothing. If it prints a version such as `V1001`, do not deploy the package.

`remote-deploy.sh` expects the archive to contain:

- `frontend/`
- `backend/app.jar`
- `release-metadata.json`

It activates the frontend directory, copies the backend jar, writes `deployed-release.json`, restarts systemd, and waits for health.

When automation is unavailable and the user explicitly approves a manual `scp`/SSH deployment, keep the same safety shape: upload a new jar and frontend tarball into `incoming`, stop the backend service, backup the previous jar with a timestamp, activate the new jar and frontend assets, start the backend service, reload nginx, then verify health before smoke. Prefer `StrictHostKeyChecking=accept-new`; only use legacy `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i /tmp/xiyu-prod-deploy-crm-test` if that is the only authorized access path for the environment.

## Local Packaging Hygiene

Prefer the GitHub Actions release artifact because it builds from a clean runner. When local manual packaging is necessary:

1. Remove stale backend output before packaging:

   ```bash
   rm -rf backend/target
   RELEASE_ID=<release-id> \
   PRODUCTION_API_BASE_URL=<api-url> \
   VITE_API_BASE_URL=<api-url> \
   bash scripts/release/package-release.sh
   ```

2. Check that the production API URL was injected into the frontend:

   ```bash
   rg "<host-or-ip>:<port>" ".release/<release-id>/frontend/assets"/*.js
   ```

3. Check Flyway migration versions inside the packaged jar:

   ```bash
   jar tf ".release/<release-id>/backend/app.jar" \
     | rg 'BOOT-INF/classes/db/migration-mysql/V[0-9]+__' \
     | sed -E 's#.*\/(V[0-9]+)__.*#\1#' \
     | sort \
     | uniq -d
   ```

   No output means no duplicate version is present.

4. Spot-check recently risky versions:

   ```bash
   jar tf ".release/<release-id>/backend/app.jar" \
     | rg 'BOOT-INF/classes/db/migration-mysql/V1001|BOOT-INF/classes/db/migration-mysql/V1002|BOOT-INF/classes/db/migration-mysql/V1003'
   ```

On 2026-05-28, a local manual package failed production startup because a dirty `backend/target/classes` still contained a deleted file named `V1001__alter_form_submission_audit_status_enum.sql`. The source tree only had `V1001__align_role_permissions_with_blueprint_4_2_1.sql`, but `mvn -DskipTests package` copied stale target contents into the jar. The symptom was:

```text
Found more than one migration with version 1001
```

The correct response is to stop rollout, restore the previous frontend/jar/deployment record, confirm health is back to `UP`, remove stale local build output, rebuild, inspect jar migrations, then redeploy.

## Production Smoke

The production smoke path should be read-only. Expected P0 checks include:

- Frontend home returns 200.
- `/actuator/health` is `UP`.
- Prometheus exposure matches policy: `protected`, `public`, or `skip`.
- Smoke account can login.
- `/api/auth/me` returns the logged-in user.
- Dashboard, tender list, project list, qualification/case/template list, expense list, and BAR asset list are readable.

Use:

```bash
PRODUCTION_API_BASE_URL=https://api.example.com \
PRODUCTION_WEB_BASE_URL=https://web.example.com \
PROD_SMOKE_USERNAME=<user> \
PROD_SMOKE_PASSWORD=<secret> \
node scripts/release/run-prod-smoke.mjs
```

Any P0 failure is `NO-GO`.

## Go-Live Checklist Summary

Before production:

- Candidate commit frozen.
- Frontend build passes.
- Backend compile/tests pass for affected scope.
- Architecture gates pass for backend architecture changes.
- E2E/API smoke passes on real API.
- MySQL 8.0 baseline and Flyway path confirmed.
- Database backup is created and restorable.
- Monitoring and alerting are configured or explicitly deferred.
- UAT/signoff state is known.
- Production GitHub secrets and vars are configured.

During production:

- Record commit, release id, operator, start time, and maintenance window.
- Execute preflight.
- Run or verify database backup.
- Activate backend and frontend artifacts.
- Check health, smoke, and frontend availability.
- Record deployed release metadata.

After production:

- Watch the first 30 minutes.
- Confirm login, dashboard, tender/project list, knowledge flow, resource approval, and BAR certificate borrowing.
- Confirm no P0/P1 alerts, stable DB pool, and expected Prometheus protection.
- Store report under `docs/reports/` when the project expects archival output.

## Rollback Posture

Deployment is not ready unless rollback anchors exist:

- Previous git tag or commit.
- Previous frontend artifact.
- Previous backend jar.
- Database backup and Flyway version.
- Environment variable snapshot.
- Clear owner for frontend, backend, DBA, and release decision.

Rollback triggers:

- Database migration fails.
- Backend cannot start.
- Login core flow fails.
- Core APIs emit sustained 5xx.
- Core business cannot recover inside the maintenance window.

Use project `docs/release/ROLLBACK.md` as source of truth. Never run `flyway clean` in production. For database restoration, require explicit user confirmation of target database and backup file.
