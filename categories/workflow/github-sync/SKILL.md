---
name: github-sync
description: GitHub 与 Gitee 双向代码同步技能（西域数智化投标管理平台）。用于 AI Coding 工具（Cursor/Codex/Claude 等）在 GitHub 远端改代码后同步回本地 Gitee 主仓库，或反向推送本地代码到 GitHub 供 AI 工具使用。触发场景：用户提到"同步 GitHub"、"拉取 AI 改动"、"GitHub 代码合回 Gitee"、"推 GitHub 镜像"、"AI Cursor 改的代码怎么拉回来"、"github-sync"、"同步远端 AI 改动"。
---

# GitHub Sync

## 定位

**Gitee 为主仓库（source of truth），GitHub 为 AI 协作入口 + 镜像备份。**

```
AI Coding 工具 → GitHub 分支/PR → 本地 fetch → 审核合并 → 推回 Gitee（origin）
                                                              ↓
                                                        GitHub 镜像同步
```

## Remote 配置

| Remote 名 | URL | 用途 |
|---|---|---|
| `origin` | `git@gitee.com:allinai888/bid.git` | **主仓库**：PR / CI / 协作走这里 |
| `github` | `git@github-bid:yzcynk5vtp-ship-it/bid.git` | **AI 协作入口 + 镜像**：AI 工具改代码，本地同步 |

## SSH 配置

- Gitee：`~/.ssh/id_ed25519`（默认 key）
- GitHub：`~/.ssh/github_bid_mirror` + `~/.ssh/config` 中的 `Host github-bid`（`IdentitiesOnly yes`）
- GitHub 账户：`yzcynk5vtp-ship-it`（deploy key 绑定 `bid` 仓库，已开启 write access）

## 工作流

### 场景 1：从 GitHub 拉取 AI 工具的改动（最常用）

AI Coding 工具（Cursor/Codex/Claude 等）在 GitHub 上创建分支或直接 push 到 main，本地同步回 Gitee。

```bash
# 1. 拉取 GitHub 远端
git fetch github

# 2. 查看 GitHub 上有哪些新分支
git branch -r | grep github/

# 3. 对比 GitHub main 与本地 main 的差异
git log --oneline main..github/main
git diff main..github/main --stat

# 4. 审查 AI 改动（基于 GitHub 分支创建本地审查分支）
git checkout -b review/ai-<feature> github/<ai-branch>

# 5. 审查 OK 后，合入本地 main
git checkout main
git merge review/ai-<feature>
# 或 cherry-pick 特定 commit
git cherry-pick <commit-hash>

# 6. 推送到 Gitee（主仓库）
git push origin main

# 7. 清理审查分支
git branch -d review/ai-<feature>
```

### 场景 2：GitHub main 直接有提交，同步回 Gitee

AI 工具直接 push 到 GitHub main 分支，需要同步回 Gitee。

```bash
# 1. 拉取 GitHub main
git fetch github

# 2. 查看差异
git log --oneline main..github/main

# 3. 合并 GitHub main 到本地 main
git checkout main
git merge github/main

# 4. 推送到 Gitee
git push origin main
```

### 场景 3：本地代码推到 GitHub 供 AI 工具使用

本地有新改动，需要让 GitHub 上的 AI 工具能拉到最新代码。

```bash
# 推送 Gitee（主仓库）
git push origin main

# 推送 GitHub（供 AI 工具拉取）
git push github main
```

### 场景 4：双向同步（完整流程）

确保 Gitee 和 GitHub 完全一致。

```bash
# 1. 先拉取两端最新
git fetch origin
git fetch github

# 2. 对比差异
echo "Gitee:  $(git rev-parse origin/main)"
echo "GitHub: $(git rev-parse github/main)"

# 3. 如果 Gitee 更新（本地有新提交）
git push github main

# 4. 如果 GitHub 更新（AI 工具有新提交）
git checkout main
git merge github/main
git push origin main

# 5. 验证两端一致
git fetch origin github
echo "Gitee:  $(git rev-parse origin/main)"
echo "GitHub: $(git rev-parse github/main)"
```

## 安全约定

1. **Gitee 是唯一 source of truth**：所有最终代码以 Gitee main 为准
2. **GitHub 改动必须审查**：AI 工具的改动不能直接合入，必须本地审查
3. **门禁对两端生效**：`pre-push-gate.sh` 等门禁对 `origin` 和 `github` 都生效
4. **冲突优先保留 Gitee**：双向冲突时，以 Gitee 为准，GitHub 重新同步
5. **不绕过门禁**：禁止 `--no-verify`，如需绕过必须用 `XIYU_ALLOW_GIT_NO_VERIFY=1` 并说明原因

## 快速诊断

```bash
# 查看双仓库状态
git remote -v
git fetch origin github
echo "Gitee:  $(git rev-parse origin/main)"
echo "GitHub: $(git rev-parse github/main)"
echo "本地:   $(git rev-parse main)"

# 查看 GitHub 新分支
git fetch github
git branch -r | grep github/

# 测试 GitHub 连通性
ssh -T github-bid
```

## 常见问题

### Q: deploy key 能创建 PR 吗？

**不能。** deploy key 只能 push/pull 代码，无法通过 git 协议创建 PR（PR 是 GitHub API 操作）。如果需要在 GitHub 创建 PR，需要账户级 token 或登录 `yzcynk5vtp-ship-it` 账户在网页操作。

### Q: AI 工具改的代码怎么审查？

```bash
git fetch github
git checkout -b review/ai-fix github/<branch>
# 本地跑测试
npm run build
cd backend && mvn test
# 审查 OK 后合入
git checkout main && git merge review/ai-fix
git push origin main
```

### Q: GitHub 和 Gitee 冲突怎么办？

以 Gitee 为准：
```bash
git push github main --force-with-lease  # 用 Gitee 的版本覆盖 GitHub
```

注意：`--force-with-lease` 需要显式确认，且会写入审计日志。

### Q: 如何让 AI 工具拉到最新代码？

确保 GitHub main 与 Gitee 同步：
```bash
git push github main
```
AI 工具从 GitHub clone 后即可获得最新代码。
