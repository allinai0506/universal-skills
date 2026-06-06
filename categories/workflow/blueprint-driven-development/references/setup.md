# Setup — 首次使用

> 当用户首次启动本 skill 或缺失关键配置时，加载此文件。

---

## 1. 检查配置文件

```bash
WORKTREE=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
CONFIG="$WORKTREE/.blueprint-config.json"

if [ -f "$CONFIG" ]; then
  echo "✅ 找到配置：$CONFIG"
  source "$CONFIG" 2>/dev/null || true
else
  echo "⚠️  未找到配置文件，使用默认值"
fi
```

---

## 2. 检查/创建检查点

```bash
WORKTREE=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
CHECKPOINT="$WORKTREE/.blueprint-checkpoint.json"

if [ ! -f "$CHECKPOINT" ]; then
  echo '{"section":null,"phase":1,"phases_done":[],"worktree":"'"$WORKTREE"'"}' > "$CHECKPOINT"
  echo "✅ 检查点文件已创建：$CHECKPOINT"
else
  echo "📋 检查点已存在：$(cat "$CHECKPOINT")"
fi
```

---

## 3. 检查数据目录

```bash
DATA_DIR="${CLAUDE_PLUGIN_DATA:-$WORKTREE/.blueprint-data}"
mkdir -p "$DATA_DIR"
echo "📁 数据目录：$DATA_DIR"
```

---

## 4. 缺失配置时的交互

如果关键配置缺失，使用 `AskQuestion` 向用户提问：

**必填项**（缺失则无法继续）：
1. 飞书蓝图文档 URL 或 doc token
2. 目标小节编号（如 4.2.1）

**可选项**（可从 dev-env.sh 推断）：
- `BACKEND_PORT`、`FRONTEND_PORT`、`DB_NAME`

**使用示例**：

```javascript
// 当 CONFIG 不存在或缺少必填字段时
AskQuestion({
  questions: [{
    id: "blueprint_info",
    prompt: "请提供飞书蓝图文档信息",
    options: [
      { id: "provide_url", label: "提供文档 URL" },
      { id: "provide_token", label: "提供文档 token" }
    ]
  }]
})
```

---

## 5. 从 dev-env.sh 推断配置

如果配置缺失但 `scripts/dev-env.sh` 存在，自动读取：

```bash
WORKTREE=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
if [ -f "$WORKTREE/scripts/dev-env.sh" ]; then
  source "$WORKTREE/scripts/dev-env.sh"
  echo "推断配置：BACKEND_PORT=$BACKEND_PORT, FRONTEND_PORT=$FRONTEND_PORT"
fi
```

---

## 6. 初始化完成检查清单

- [ ] `.blueprint-checkpoint.json` 存在
- [ ] `.blueprint-data/` 目录存在
- [ ] 蓝图 URL/token 已获取
- [ ] 目标小节编号已确认

全部完成后，进入 Phase 1。
