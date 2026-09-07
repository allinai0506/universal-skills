# Memory Backend — Ollama + MemU 本地运维（启停说明）

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

## 三个坑（spike 实测）

1. `pip install memu` 是错的（安卓模拟器），正主叫 **`memu-cli`**。
2. 本机 shell 有 SOCKS 代理变量，httpx 会劫持对 localhost 的调用而报错
   `socksio缺失` ——调 `memu*` 前先 `env -u ...` strip（定时任务环境干净，不受影响）。
   检索指令（各项目 AGENTS.md）里已内含 strip 前缀。
3. 检索一律设阈值（建议 score ≥ 0.5）：memu 对无关问题也会返回，低分丢弃。
