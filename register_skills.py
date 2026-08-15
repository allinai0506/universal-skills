#!/usr/bin/env python3
import json
import os

config_path = os.path.expanduser("~/.trae-cn/skill-config.json")

with open(config_path, 'r') as f:
    config = json.load(f)

# 所有 superpowers 技能列表
superpowers_skills = [
    "brainstorming",
    "deep-dive",
    "deep-interview",
    "dispatching-parallel-agents",
    "executing-plans",
    "finishing-a-development-branch",
    "receiving-code-review",
    "requesting-code-review",
    "root-cause-hunter",
    "subagent-driven-development",
    "systematic-debugging",
    "test-driven-development",
    "using-git-worktrees",
    "using-superpowers",
    "verification-before-completion",
    "writing-plans",
]

# 将所有 superpowers 技能注册到 managedSkills
for skill in superpowers_skills:
    if skill not in config["managedSkills"]:
        # 使用 "local" 标记，或者 "marketplace"（如果适用）
        # 这里我们用一个假的 marketplace 标记，或者直接用 local
        config["managedSkills"][skill] = "local"

# 保存
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("=== skill-config.json 已更新 ===")
print(f"已注册的 superpowers 技能:")
for skill in superpowers_skills:
    if skill in config["managedSkills"]:
        print(f"  - {skill}: {config['managedSkills'][skill]}")
