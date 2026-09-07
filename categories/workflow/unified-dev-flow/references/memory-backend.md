# Memory Backend — Ollama + MemU 本地运维（启停说明 + Rollout）

Spike 结论：MemU 作召回索引（SQLite），bge-m3 作本地 embedding，
Markdown/TSV 永远是 source of truth。本页只讲本机 backend 的启停，
记忆选型论证见 implementation-notes.md（MemU spike 条目）。

## 架构一览

```
Agent (任意工具) ──memu retrieve──▶ ~/.memu/memu.sqlite3 (记忆索引)
                         │ embedding
                         ▼
               Ollama :11434 (bge-m3, 1.2GB, 本地免费)
Markdown/TSV (各项目内) ──memu commit──▶ 同上（手动入库，显式可审计）
session-brief.py ──直读──▶ ck / wiki / ledger / decisions.tsv（不经过 MemU，逃生通道）
```

## 启动

```bash
# 首次（已做过则跳过）
brew install ollama && ollama pull bge-m3

# 每次开机后
(ollama serve > /tmp/ollama.log 2>&1 &)
curl -s http://localhost:11434/api/tags | head -c 120  # 有输出即活着

# memu 配置（~/.memu/config.env，chmod 600，API_KEY 只是占位符）
# MEMU_MEMORY_MODE=local
# MEMU_DB=/Users/user/.memu/memu.sqlite3
# MEMU_EMBED_PROVIDER=openai
# MEMU_BASE_URL=http://localhost:11434/v1
# MEMU_EMBED_MODEL=bge-m3
# MEMU_API_KEY=local-placeholder

# 自检（注意先 strip 代理变量，见下）
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
  memu-agent doctor
```

## 停止（腾资源）

```bash
pkill -f "ollama serve"   # 释放内存；模型文件留磁盘（~/.ollama，约 1.2GB）
# 连模型文件都要删：ollama rm bge-m3
```

## Rollout：主力项目 AGENTS.md 检索指令 + Codex/Qoder 定时挖矿

### 1. 各仓 AGENTS.md 统一追加（不改仓库别的东西）

```markdown
## 长期记忆检索（MemU）

每次 SessionStart / 开工前：
```bash
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
  memu-agent retrieve "your query here" --score 0.5
```
- `score < 0.5` 直接丢弃（无关噪音多）
- 文件永远是 source of truth；MemU 只做索引，不造新轮子
```

### 2. Codex 定时挖矿（launchd，每天一次）

`~/Library/LaunchAgents/com.user.memu-codex.plist`（chmod 644，`launchctl load`）：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.user.memu-codex</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/miniconda3/bin/memu-codex</string>
    <string>prepare</string>
    <string>--session-dir</string><string>~/.codex/sessions</string>
    <string>--max-jobs</string><string>20</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>3</integer><key>Minute</key><integer>0</integer></dict>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/opt/miniconda3/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>StandardOutPath</key><string>/tmp/memu-codex.log</string>
  <key>StandardErrorPath</key><string>/tmp/memu-codex.err</string>
</dict>
</plist>
```

Commit 同步可另行周一手动跑：

```bash
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
  memu-codex commit
```

### 3. Qoder-CN 定时挖矿（launchd，每天 03:15）

`~/Library/LaunchAgents/com.user.memu-qoder-cn.plist`（同理）：

```xml
<key>ProgramArguments</key>
<array>
  <string>/opt/miniconda3/bin/memu-qoder</string>
  <string>prepare</string>
  <string>--session-dir</string><string>~/.qoder-cn/sessions</string>
  <string>--max-jobs</string><string>20</string>
</array>
<key>StartCalendarInterval</key>
<dict><key>Hour</key><integer>3</integer><key>Minute</key><integer>15</integer></dict>
```

### 4. 验收标准

- `memu-agent doctor` 绿（Ollama 连通 + memu.sqlite3 可写）
- 各仓 AGENTS.md 检索指令已追加（grep `memu-agent retrieve` 命中）
- Codex/Qoder plist 已 `launchctl load` 且 `/tmp/memu-*.log` 3:xx 有 prepare 输出
- `memu-agent retrieve "known topic" --score 0.5` 返回命中段（非空）

### 5. 坑（spike 实测复现）

1. `pip install memu` 是错的（安卓模拟器），正主叫 **`memu-cli`**。
2. 本机 shell 有 SOCKS 代理变量，httpx 会劫持对 localhost 的调用而报错
   `socksio缺失` ——调 `memu*` 前先 `env -u ...` strip（定时任务环境干净，不受影响）。
   检索指令（各项目 AGENTS.md）里已内含 strip 前缀。
3. 检索一律设阈值（建议 score ≥ 0.5）：memu 对无关问题也会返回，低分丢弃。

## 三个坑（spike 实测）

1. `pip install memu` 是错的（安卓模拟器），正主叫 **`memu-cli`**。
2. 本机 shell 有 SOCKS 代理变量，httpx 会劫持对 localhost 的调用而报错
   `socksio缺失` ——调 `memu*` 前先 `env -u ...` strip（定时任务环境干净，不受影响）。
   检索指令（各项目 AGENTS.md）里已内含 strip 前缀。
3. 检索一律设阈值（建议 score ≥ 0.5）：memu 对无关问题也会返回，低分丢弃。
