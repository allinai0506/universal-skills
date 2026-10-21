# gitee-pr-helper · 本仓库用法

Gitee API v5 的 PR 辅助脚本（`list` / `create` / `check` / `merge` / `approve`），
源自 `~/bid-product/scripts/gitee-pr-helper.sh`，本仓库副本把默认仓库名改为
`general-skills`（上游默认是 `bid`）。

## 为什么放在仓库里

此前建 PR 时需要从其他项目临时复制脚本，且必须显式传 `GITEE_REPO=general-skills`
才能用（否则请求会打到 `bid` 仓库，报 `源分支 ... 不存在`）。放进仓库后默认即对。

## 常用命令

```bash
# 列出当前分支的开放 PR
./scripts/gitee-pr-helper.sh list

# 创建 PR（当前分支 → main）
./scripts/gitee-pr-helper.sh create

# 指定标题与描述
GIT_PR_TITLE="feat: ..." GIT_PR_BODY="$(cat /tmp/body.md)" ./scripts/gitee-pr-helper.sh create

# 查看 PR 状态 / 合并 / 查看审核状态
./scripts/gitee-pr-helper.sh check 53
./scripts/gitee-pr-helper.sh merge 53
./scripts/gitee-pr-helper.sh approve 53
```

## 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `GITEE_TOKEN` | 自动解析链 | Gitee 个人访问令牌 |
| `GITEE_OWNER` | `allinai888` | 仓库属主 |
| `GITEE_REPO` | `general-skills` | 仓库名（**本仓库默认**） |
| `GITEE_BASE_BRANCH` | `main` | 目标分支 |
| `GIT_PR_TITLE` | 从 commit message 提取 | PR 标题 |
| `GIT_PR_BODY` | 从 commit body 提取 | PR 描述 |

## 与 S6 门禁的关系（重要）

`create` 会先调用 `unified-dev-flow` 的 `--guard-pr` 物理门禁：

```
[gitee-pr] 🔍 检查 S5 验证与 S6 Code Review 交付凭证...
✅ [unified-dev-flow 门禁放行] S6 Code Review 验证通过: verdict=MERGE_READY
```

**没有 `.omc/verify-<session>.md` 与合格的 `.omc/review-<session>.md`（`verdict: MERGE_READY`）
就无法建 PR** —— 这不是脚本的软检查，而是 `entry-gate-check.py` 的硬拦截，绕过它
没有意义。逃生阀 `UNIFIED_DEV_FLOW_SKIP_REVIEW=1` 仅限生产抢修，且会留审计记录。

**生效条件（须知）**：该拦截仅在分支名匹配 `agent/` / `feat/` / `fix/` 前缀时触发，
且门禁脚本需可被找到 —— 优先 `~/.claude/scripts/entry-gate-check.py`，缺失时回退到
仓库内 `categories/workflow/unified-dev-flow/scripts/entry-gate-check.py`。若两者都
不存在，拦截会被跳过（此时请自行确认已完成 S6）。

## Token 解析

`GITEE_TOKEN` 未显式注入时，`scripts/gitee-token.sh` 按以下顺序自动解析：

1. `$GITEE_TOKEN` 环境变量
2. `~/.config/xiyu/credentials.env`（推荐，chmod 600）
3. `~/.zshenv` 中的 export 行
4. `git credential fill`（最后手段）

申请令牌：https://gitee.com/profile/personal_access_tokens

## 远端名注意

脚本用 `origin` 作为默认远端名，而本仓库的远端名为 `gitee`。首次使用请先设置
upstream：

```bash
git push -u gitee <branch>
```

否则 `create` 会提示「分支尚未推送到远端」。
