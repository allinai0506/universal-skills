#!/usr/bin/env python3
"""扫描 categories/ 下所有一层技能，按分类生成 SKILLS-INDEX.md 速查表。

用法:
    python3 scripts/generate-skills-index.py [输出路径]

默认输出到仓库根目录 SKILLS-INDEX.md。
只索引 categories/<分类>/<技能>/SKILL.md 两层结构，以及
categories/<分类>/SKILL.md 单文件技能（如 security-review）。
"""
import csv
import os
import re
import sys
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES = os.path.join(REPO, "categories")
CSV_PATH = os.path.join(REPO, "scripts", "skills-desc-zh.csv")


def load_desc_zh():
    """读取中文用途说明 CSV，返回 {(cat, skill): desc_zh}。"""
    mapping = {}
    if not os.path.isfile(CSV_PATH):
        return mapping
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cat = (row.get("cat") or "").strip()
            skill = (row.get("skill") or "").strip()
            desc = (row.get("desc_zh") or "").strip()
            if cat and skill and desc:
                mapping[(cat, skill)] = desc
    return mapping

# 分类说明（key 为目录名，value 为一行简介）
CATEGORY_DESC = {
    ".system": "元工具（创建 / 安装技能）",
    "ai": "AI 相关模式",
    "architecture": "架构模式",
    "coding": "编码规范与模式",
    "data": "数据 / 数据库模式",
    "debugging": "调试方法论",
    "deployment": "部署模式",
    "engineering": "mattpocock 工程技能",
    "frameworks": "框架模式",
    "gstack": "gstack 发行版定制技能",
    "imported": "自动发现的第三方技能",
    "languages": "各语言规范",
    "misc": "其他",
    "pstack": "poteto 工程方法论",
    "refactoring": "重构实践",
    "security-review": "安全审查",
    "testing": "测试",
    "tools": "工具集成",
    "ui-ux": "前端设计",
    "workflow": "开发流程",
}

# 来源分类：按「来源」把技能分为
#   1) 公开技能包（外部大神编写、成体系、有使用逻辑）
#   2) 自建 / 单个技能（自己创建或单独引入）
# 映射 key=分类目录，value=所属来源。后续要调整某分类的来源，改这里即可。
PUBLIC_PACKAGES = {
    ".system": "anthropics 官方工具",
    "tools": "anthropics 官方工具",
    "engineering": "mattpocock / skills",
    "pstack": "poteto 工程方法论",
    "gstack": "gstack 发行版",
    "ui-ux": "前端设计",
}
# 来源分组的小节标题（用于公开技能包；自建技能直接按分类列）
PACKAGE_NOTE = {
    "anthropics 官方工具": "安装能力 / 文档 / PDF / 浏览器工具",
    "mattpocock / skills": "需求→规格→工单→实现→验证的完整工程闭环",
    "poteto 工程方法论": "poteto-mode 工作流 + 21 条工程原则",
    "gstack 发行版": "Everything Claude Code 全家桶定制技能",
    "前端设计": "前端界面设计技能",
}


def parse_sillskip(md_path):
    """解析 SKILL.md frontmatter 的 name 与 description。"""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
    # 只取 frontmatter（--- 之间）
    m = re.match(r"\A---\s*\n(.*?)\n---", content, re.DOTALL)
    fm = m.group(1) if m else ""
    name = ""
    desc = ""
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(name|description)\s*:\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if key == "name" and not name:
                name = val.strip("\"'")
            elif key == "description" and not desc:
                # 块标量（description: > / | / >- / |-）：收集后续缩进行拼成一段
                if val and val[0] in ">|":
                    folded = []
                    j = i + 1
                    while j < len(lines) and (lines[j].startswith(" ") or lines[j].startswith("\t")):
                        folded.append(lines[j].strip())
                        j += 1
                    desc = " ".join(folded)
                    i = j - 1
                else:
                    desc = val.strip("\"'")
        i += 1
    return name, desc


def render_table(rows, cat, desc_zh):
    """rows: list of (skill_name, description)。返回 markdown 表格。
    用途列优先显示中文说明，缺失时回退到原 description。"""
    lines = ["| 技能 | 用途 |", "| --- | --- |"]
    for skill, desc in rows:
        zh = desc_zh.get((cat, skill), "")
        text = zh or desc
        text = (text or "（无说明）").replace("|", "\\|").replace("\n", " ").strip()
        lines.append(f"| `{skill}` | {text} |")
    return "\n".join(lines)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "SKILLS-INDEX.md")
    desc_zh = load_desc_zh()

    groups = []  # (cat, rows)
    total = 0
    for cat in sorted(os.listdir(CATEGORIES)):
        catp = os.path.join(CATEGORIES, cat)
        if not os.path.isdir(catp):
            continue
        rows = []
        # 单文件技能：categories/<分类>/SKILL.md
        single = os.path.join(catp, "SKILL.md")
        if os.path.isfile(single):
            name, desc = parse_sillskip(single)
            rows.append((cat, desc or "（安全审查）"))
        # 两层结构：categories/<分类>/<技能>/SKILL.md
        for skill in sorted(os.listdir(catp)):
            sp = os.path.join(catp, skill)
            md = os.path.join(sp, "SKILL.md")
            if os.path.isdir(sp) and os.path.isfile(md):
                _, desc = parse_sillskip(md)
                rows.append((skill, desc))
        if rows:
            total += len(rows)
            groups.append((cat, rows))

    # 按来源分组：公开技能包(按包) / 自建(按原分类)
    public = {}  # source_name -> [(cat, rows)]
    self_made = []  # [(cat, rows)]
    for cat, rows in groups:
        src = PUBLIC_PACKAGES.get(cat)
        if src:
            public.setdefault(src, []).append((cat, rows))
        else:
            self_made.append((cat, rows))

    lines = ["# SKILLS-INDEX", ""]
    lines.append(f"> 技能来源速查表 · 自动生成于 {datetime.now():%Y-%m-%d %H:%M} · 共 {total} 个一级技能。")
    lines.append("> 按「来源」检索：公开技能包（外部大神编写的成套技能） / 自建・单个技能。")
    lines.append("> 技能由 AI 按 description 自动触发，无需记住名字。")
    lines.append("")

    # 目录
    lines.append("按来源检索：")
    toc_parts = ["[一、公开技能包](#一公开技能包)", "[二、自建・单个技能](#二自建单个技能)"]
    lines.append(" · ".join(toc_parts))
    lines.append("")

    # 一、公开技能包
    lines.append("## 一、公开技能包")
    lines.append("_外部技术大神编写的成套技能，每个包内部技能有使用逻辑。_")
    lines.append("")
    public_pkgs = sorted(public.keys())
    for pkg in public_pkgs:
        anchor = re.sub(r"[^\w\u4e00-\u9fff]+", "-", pkg).strip("-")
        lines.append(f"### {pkg}")
        note = PACKAGE_NOTE.get(pkg, "")
        if note:
            lines.append(f"_{note}_")
        lines.append("")
        for cat, rows in public[pkg]:
            note2 = CATEGORY_DESC.get(cat, "")
            if note2:
                lines.append(f"**{cat}** _({note2})_")
            lines.append("")
            lines.append(render_table(rows, cat, desc_zh))
            lines.append("")
    lines.append("---")
    lines.append("")

    # 二、自建 / 单个技能
    lines.append("## 二、自建・单个技能")
    lines.append("_自己创建或单独引入的技能，按原分类组织。_")
    lines.append("")
    for cat, rows in self_made:
        lines.append(f"### {cat}")
        note = CATEGORY_DESC.get(cat, "")
        if note:
            lines.append(f"_{note}_")
        lines.append("")
        lines.append(render_table(rows, cat, desc_zh))
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"生成完成：{out_path}（{total} 个技能，公开包 {len(public_pkgs)} 个，自建分类 {len(self_made)} 个）")


if __name__ == "__main__":
    main()