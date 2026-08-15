#!/usr/bin/env python3
"""低频技能清理分析脚本。

基于 gstack 的 ~/.gstack/analytics/skill-usage.jsonl 统计各技能使用次数，
结合 categories/ 下全部技能与中文说明，列出「低频 / 零使用」候选以便清理。

用法:
    python3 scripts/analyze-skill-usage.py [选项]

选项:
    --usage PATH    使用记录文件路径（默认 ~/.gstack/analytics/skill-usage.jsonl）
    --days N        最近 N 天未使用视为低频（默认 90）
    --min M         使用次数 < M 视为低频（默认 1，即零使用）
    --json          以 JSON 输出统计
    --delete        实际删除低频技能目录（默认仅打印清单，不删除）
    --dry-run       显式 dry-run（默认行为，仅打印）
"""
import argparse
import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES = os.path.join(REPO, "categories")
CSV_PATH = os.path.join(REPO, "scripts", "skills-desc-zh.csv")
DEFAULT_USAGE = os.path.expanduser("~/.gstack/analytics/skill-usage.jsonl")


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def load_usage(path):
    """返回 (counts, last)：skill -> 次数，skill -> 最近使用 datetime。"""
    counts, last = {}, {}
    if not os.path.isfile(path):
        return counts, last
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        skill = d.get("skill")
        if not skill:
            continue
        counts[skill] = counts.get(skill, 0) + 1
        t = parse_ts(d.get("ts", ""))
        if t and (skill not in last or t > last[skill]):
            last[skill] = t
    return counts, last


def load_desc_zh():
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


def scan_skills():
    """返回 [(cat, skill, path)]，含单文件技能。"""
    out = []
    for cat in sorted(os.listdir(CATEGORIES)):
        catp = os.path.join(CATEGORIES, cat)
        if not os.path.isdir(catp):
            continue
        single = os.path.join(catp, "SKILL.md")
        if os.path.isfile(single):
            out.append((cat, cat, single))
        for skill in sorted(os.listdir(catp)):
            sp = os.path.join(catp, skill)
            md = os.path.join(sp, "SKILL.md")
            if os.path.isdir(sp) and os.path.isfile(md):
                out.append((cat, skill, sp))
    return out


def lookup(counts, last, skill):
    """usage 中技能名可能带/不带 gstack- 前缀，三种形式都匹配。"""
    stripped = re.sub(r"^gstack-", "", skill)
    keys = {skill, "gstack-" + stripped, stripped}
    c = sum(counts.get(k, 0) for k in keys)
    lt = None
    for k in keys:
        t = last.get(k)
        if t and (lt is None or t > lt):
            lt = t
    return c, lt


def main():
    ap = argparse.ArgumentParser(description="低频技能清理分析")
    ap.add_argument("--usage", default=DEFAULT_USAGE)
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--min", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--delete", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    counts, last = load_usage(args.usage)
    desc = load_desc_zh()
    skills = scan_skills()
    now = datetime.now().astimezone()

    rows = []
    for cat, skill, path in skills:
        c, lt = lookup(counts, last, skill)
        rows.append({
            "cat": cat, "skill": skill, "path": path,
            "count": c, "last": lt.isoformat() if lt else None,
            "desc": desc.get((cat, skill), ""),
        })

    # 低频判定：次数 < min 或 最近使用早于 now - days
    cutoff = now - __import__("datetime").timedelta(days=args.days)

    def is_low(r):
        if r["count"] < args.min:
            return True
        if r["last"]:
            t = parse_ts(r["last"])
            # usage 时间戳统一转成带时区再比较，避免 naive/aware 混比报错
            if t and t.astimezone() < cutoff:
                return True
        return False

    low = [r for r in rows if is_low(r)]
    used = sorted([r for r in rows if r["count"] > 0], key=lambda r: r["count"], reverse=True)

    if args.json:
        print(json.dumps({
            "total": len(rows), "used": len(used),
            "low_frequency": low, "top_used": used,
        }, ensure_ascii=False, indent=2))
        return

    print(f"技能总数: {len(rows)}   有使用记录: {len(used)}   低频候选: {len(low)}\n")
    print("==" * 30)
    print("使用最多的技能（有记录，按次数降序）:")
    for r in used[:15]:
        print(f"  {r['count']:>3} 次  {r['last'][:10] if r['last'] else '--':<12} [{r['cat']}] {r['skill']}")
    if not used:
        print("  （无任何使用记录）")

    print("\n" + "==" * 30)
    print(f"低频 / 零使用候选（{len(low)} 个，阈值: 次数<{args.min} 或 最近{args.days}天未用）:")
    for r in low:
        us = f"{r['count']}次" if r["count"] > 0 else "零使用"
        last = r["last"][:10] if r["last"] else "从未使用"
        print(f"  {us:<7} 最近:{last:<12} [{r['cat']}] {r['skill']}  {r['desc']}")

    if args.delete:
        if args.dry_run:
            print("\n[dry-run] 未删除任何目录。去掉 --dry-run 或直接传 --delete 才会真正删除。")
            return
        # 删除前要求显式二次确认，避免误删大量技能
        print(f"\n将删除 {len(low)} 个低频技能项:")
        for r in low:
            print(f"  rm -rf {r['path']}")
        try:
            confirm = input(f"确认删除上述 {len(low)} 项? 输入 yes 继续: ")
        except EOFError:
            confirm = ""
        if confirm.strip().lower() != "yes":
            print("已取消，未删除任何内容。")
            return
        removed = 0
        for r in low:
            p = r["path"]
            if os.path.isfile(p):
                os.remove(p)
            else:
                shutil.rmtree(p, ignore_errors=True)
            removed += 1
        print(f"已删除 {removed} 项。建议运行: python3 scripts/generate-skills-index.py && ./sync.sh --no-projects")
    else:
        print("\n（未删除。确认后运行: python3 scripts/analyze-skill-usage.py --delete）")


if __name__ == "__main__":
    main()