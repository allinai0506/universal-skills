# Bug 根因诊断与防回归技能包

版本：1.0.0。用于 Coding Agent 的本地/仓库级技能，不是自动修改生产系统的服务。

核心交付：把“错误消失”与“致错机制被验证并阻断”分开验收。
入口在 `SKILL.md`；详解、模板、校验脚本和演示按需加载。

## 安装：先在一个仓库使用

解压后，保留完整的 `root-cause-debugging` 目录；不要只复制 SKILL.md。

| 使用工具 | 项目级目录 | 个人级目录 |
| --- | --- | --- |
| Codex | `.agents/skills/root-cause-debugging/` | `~/.agents/skills/root-cause-debugging/` |
| Claude Code | `.claude/skills/root-cause-debugging/` | `~/.claude/skills/root-cause-debugging/` |
| OpenCode | `.opencode/skills/root-cause-debugging/` | `~/.config/opencode/skills/root-cause-debugging/` |

OpenCode 也支持 `.agents/skills` 和 `.claude/skills`。同一工具只保留一份同名技能，避免版本漂移。
上述路径依据官方文档于 2026-09-25 核对；来源在 references/sources.md。
这是文件夹安装包，不是已发布到任何技能商店的插件；不同工具的实际加载需在本地确认。

以 Codex 项目级安装为例：在目标仓库根目录，把文件夹复制进 `.agents/skills/`。
最终路径必须是 `.agents/skills/root-cause-debugging/SKILL.md`，不要多套一层解压目录。
已有同名目录时先对比与备份，不直接覆盖。新开会话确认技能可见。

## 直接使用

Codex CLI / IDE：

```text
$root-cause-debugging
修复下面的 Bug：<实际症状、输入、日志或 Issue>。
先复现并验证致错机制，再做最小完整修复。
不要把测试变绿当成根因证明；最后说明具体阻断了哪条复发路径。
```

Claude Code：

```text
/root-cause-debugging
请诊断这个反复回归的问题：<描述>。本轮只取证和定位，不修改业务实现。
```

OpenCode：

```text
加载 root-cause-debugging 技能，验收这个 Bug 修复。
核对真实路径、修前失败/修后通过证据、相邻行为和剩余风险。
```

只诊断时明确“只诊断”；要求修复时，Agent 可在原授权范围内完成全部阶段，无需阶段性重复确认。
问题描述、仓库、测试条件已经提供时直接读取，不重复索要。无法取得的证据如实标注。

## 包含内容

- `SKILL.md`：三道验收关口、任务模式、禁止行为、按需加载索引。
- `references/`：溯源、防复发、独立验收、现有工程协议接入和原始资料。
- `templates/`：完整证据 JSON 模板与人类可读交付模板。
- `scripts/check_evidence.py`：只读证据完整性校验器，Python 3.9+，无第三方依赖。
- `tests/`：校验器的自动化测试。
- `examples/atomic-archive/`：合成归档场景，旧代码失败、新代码通过、恢复旧代码再失败。
- `VALIDATION.md`：本次打包实际执行的检查与未验证范围。

## 默认流程

```text
G1 事实与复现
    ↓
G2 因果验证 + 修改前影响分析
    ↓
G3 最小完整修复 + 可执行约束 + 反证/回归验收
```

根因不是“越底层越好”。任务是找出一个经证据支持、能解释目标失败、可被修正的致错机制。
数据库约束、领域校验和测试并非每次必须全部新增；复用已有约束并补充缺失的有效防护。

## 证据模板与命令

普通小问题用简短记录即可。涉及状态、持久化、并发、权限、迁移、跨服务或反复回归时用 JSON。
将 `templates/evidence.json` 复制到项目既有缺陷记录目录，替换全部占位符，并保留可审阅的脱敏证据。
下例在技能目录运行；将 `<记录.json>` 替换为真实路径。

```bash
python3 scripts/check_evidence.py <记录.json> --phase diagnose
python3 scripts/check_evidence.py <记录.json> --phase close
python3 -m unittest discover -s tests -v
```

相对证据路径默认相对 JSON 所在目录。共享的受控证据根目录可用 `--evidence-root /绝对/路径`。
脚本拒绝越界路径、缺失文件和摘要不匹配；远程证据需保存脱敏的本地可核验副本。
脚本不会执行 JSON 中的命令、联网、修改业务代码或调整 CI。它也无法判断证据是否被故意伪造。

`--phase diagnose`：检查事实、正确性来源、因果引用、影响分析和区分实验的证据完整性。
`--phase close`：再要求修复/防护、同一场景修前失败与修后通过、相邻验证、风险项，以及高风险反证。
`checks` 中列出的修后检查都是本次验收必需项，失败/阻塞/未执行会拒绝关闭；
范围外或无法完成的其他检查写入 `limitations`，由审查者判断是否允许有条件交付。
关闭规则只针对“有证据支持的根因修复”，临时止血和证据不足的任务不能用关闭门禁结案。

## 本包不做什么

不保证 Agent 一定遵循指令，不证明所有输入都正确，不自动防止合并，也不承诺未来不再产生 Bug。
没有审计当前业务仓库，没有安装到你的电脑，没有替你合并 PR、部署或配置 HAFlow。
机械校验器不是第二位审查者。真正的验收仍需对照业务来源、实际执行产物和受影响行为。

## 从一个 Bug 开始

选一个反复修复的问题，先用 diagnose 找到证据缺口，再在获得充分证据后完成 fix。
复盘时比较同类缺陷复发率、修复引入的回归、诊断用时和验证成本；不以追问层数打分。
