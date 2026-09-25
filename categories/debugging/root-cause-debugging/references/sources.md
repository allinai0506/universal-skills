# 资料依据与设计边界

核对日期：2026-09-25。以下仅支撑对应的格式、安装或排障方法；不代表官方认可本技能，
也不证明本技能已经改善任何实际项目。三关口、证据字段与验收规则是本包的设计。

1. Agent Skills specification：目录、SKILL.md 元数据、辅助文件与按需加载。
   https://agentskills.io/specification
2. OpenAI — Build skills：Codex 本地发现目录、显式调用与技能组织。
   https://developers.openai.com/codex/skills/
   核对时跳转至 https://learn.chatgpt.com/docs/build-skills
3. Anthropic — Extend Claude with skills：Claude Code 目录与调用方式。
   https://code.claude.com/docs/en/skills
4. OpenCode — Agent Skills：支持的技能目录、元数据与发现方式。
   https://opencode.ai/docs/skills/
5. Google SRE — Effective Troubleshooting：根据系统模型建立可检验假设并用观察/实验检验。
   https://sre.google/sre-book/effective-troubleshooting/
6. Git — git-bisect：定位引入变化的版本区间及自动判定/skip 的命令行为。
   https://git-scm.com/docs/git-bisect

本包不沿用未经核实的研究统计或“只要追问到某层就证明根因”的说法。
教学案例全部是合成代码，不是对用户档案、投标或 HAFlow 当前故障的诊断。
