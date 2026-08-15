#!/usr/bin/env python3
"""从 categories/ 自动生成 Antigravity 的 GEMINI.md 全量技能表。

复用 scripts/generate-skills-index.py 的解析逻辑（SKILL.md frontmatter、
中文描述 CSV），重建 gemini-extension/universal-skills/GEMINI.md 的
Available Skills 部分，保留文件头部的 Skills root 说明与尾部的 How to Use。

用法:
    python3 scripts/generate-gemini-md.py
"""
import importlib.util
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEMINI_MD = os.path.join(REPO, "gemini-extension", "universal-skills", "GEMINI.md")

# 加载 generate-skills-index（文件名含连字符，无法直接 import）
_MODULE_PATH = os.path.join(REPO, "scripts", "generate-skills-index.py")
_spec = importlib.util.spec_from_file_location("gsi", _MODULE_PATH)
gsi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gsi)

CATEGORIES = gsi.CATEGORIES
CATEGORY_DESC = gsi.CATEGORY_DESC
parse_sillskip = gsi.parse_sillskip
render_table = gsi.render_table
load_desc_zh = gsi.load_desc_zh

# 分类 emoji（未命中的分类使用默认 📦）
CATEGORY_EMOJI = {
    ".system": "🛠️",
    "ai": "🤖",
    "architecture": "🏗️",
    "coding": "💻",
    "data": "🗄️",
    "debugging": "🐛",
    "deployment": "🚀",
    "engineering": "🧩",
    "frameworks": "🧱",
    "gstack": "🧙",
    "imported": "📥",
    "languages": "🌐",
    "misc": "🔧",
    "pstack": "🧭",
    "refactoring": "🔧",
    "security-review": "🔒",
    "testing": "🧪",
    "tools": "🔌",
    "ui-ux": "🎨",
    "workflow": "📋",
}

HEADER = """# Universal Skills

You have access to a curated set of Universal Skills stored in `~/universal-skills/categories/`.
When the user invokes a skill by name (e.g. "use tdd-workflow", "用 security-review"), read the full `SKILL.md` from the path below and follow its instructions precisely.

**Skills root:** `~/universal-skills/categories/`
**File to read per skill:** `<root>/<category>/<skill-name>/SKILL.md`

---

## Available Skills
"""

FOOTER = """
---

## How to Use a Skill

When the user references a skill by name:
1. Read `~/universal-skills/categories/<category>/<skill-name>/SKILL.md`
2. Follow its instructions as if they were part of your system prompt
3. If the skill references scripts in `scripts/` or data in `data/`, load them as needed

If you are unsure which category a skill is in, search:
```bash
find ~/universal-skills/categories -name "SKILL.md" | xargs grep -l "name: <skill-name>"
```
"""


def collect():
    """返回 [(cat, [(skill, desc)])]，skill 为技能名或''（单文件技能）。"""
    groups = []
    total = 0
    for cat in sorted(os.listdir(CATEGORIES)):
        catp = os.path.join(CATEGORIES, cat)
        if not os.path.isdir(catp):
            continue
        rows = []
        single = os.path.join(catp, "SKILL.md")
        if os.path.isfile(single):
            name, desc = parse_sillskip(single)
            rows.append((cat, desc or "（无说明）"))
        for skill in sorted(os.listdir(catp)):
            sp = os.path.join(catp, skill)
            md = os.path.join(sp, "SKILL.md")
            if os.path.isdir(sp) and os.path.isfile(md):
                _, desc = parse_sillskip(md)
                rows.append((skill, desc))
        if rows:
            total += len(rows)
            groups.append((cat, rows))
    return groups, total


def main():
    desc_zh = load_desc_zh()
    groups, total = collect()

    lines = [HEADER.rstrip("\n")]
    for cat, rows in groups:
        emoji = CATEGORY_EMOJI.get(cat, "📦")
        lines.append(f"### {emoji} {cat}")
        note = CATEGORY_DESC.get(cat, "")
        if note:
            lines.append(f"_{note}_")
        lines.append("")
        # render_table 返回 (标题行 + 分隔行 + 数据行)，直接拼接
        lines.append(render_table(rows, cat, desc_zh))
        lines.append("")
    content = "\n".join(lines).rstrip("\n") + FOOTER

    with open(GEMINI_MD, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"生成完成：{GEMINI_MD}（{total} 个技能，{len(groups)} 个分类）")


if __name__ == "__main__":
    main()