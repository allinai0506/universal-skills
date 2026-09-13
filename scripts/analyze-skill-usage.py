#!/usr/bin/env python3
"""技能使用量统计与低频清理分析脚本。

自动聚合多端 AI 工具的技能调用记录：
  1. Claude Code (~/.claude.json -> skillUsage)
  2. Qoder (~/.qoder-cn/skill-usage.json)
  3. gstack 遥测 (~/.gstack/analytics/skill-usage.jsonl)

结合 categories/ 下全部技能与中文说明，展示使用量排行与「低频 / 零使用」清理候选。

用法:
    python3 scripts/analyze-skill-usage.py [选项]

选项:
    --sort {count,recent} 排序方式（count: 按调用次数，recent: 按最近使用时间，默认 count）
    --top N               展示头部使用技能数量（默认 20）
    --days N              最近 N 天未使用视为低频（默认 90）
    --min M               使用次数 < M 视为低频（默认 1，即零使用）
    --sources S           指定数据源，逗号分隔（默认 all，可选 claude,qoder,gstack）
    --usage PATH          仅指定单个记录文件进行分析（覆写多源自动加载）
    --json                以 JSON 格式输出统计结果
    --delete              实际删除低频技能目录（默认仅打印清单，不删除）
    --dry-run             显式 dry-run（默认行为，仅打印）
"""
import argparse
import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES = os.path.join(REPO, "categories")
CSV_PATH = os.path.join(REPO, "scripts", "skills-desc-zh.csv")

DEFAULT_GSTACK = os.path.expanduser("~/.gstack/analytics/skill-usage.jsonl")
DEFAULT_CLAUDE = os.path.expanduser("~/.claude.json")
DEFAULT_QODER = os.path.expanduser("~/.qoder-cn/skill-usage.json")


def parse_iso(s):
    """解析 ISO8601 时间戳为带时区的 datetime (UTC)"""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def parse_ms(ms):
    """解析毫秒级时间戳为带时区的 datetime (UTC)"""
    if not ms or not isinstance(ms, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(ms / 1000.0, timezone.utc)
    except Exception:
        return None


def load_gstack_usage(path):
    records = []
    if not os.path.isfile(path):
        return records
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        s = d.get("skill")
        if not s:
            continue
        t = parse_iso(d.get("ts", ""))
        repo = d.get("repo", "")
        src = f"gstack ({repo})" if repo else "gstack"
        records.append({"skill": s, "count": 1, "last": t, "source": src})
    return records


def load_claude_usage(path):
    records = []
    if not os.path.isfile(path):
        return records
    try:
        data = json.load(open(path, encoding="utf-8"))
        for s, v in data.get("skillUsage", {}).items():
            cnt = v.get("usageCount", 0)
            t = parse_ms(v.get("lastUsedAt"))
            records.append({
                "skill": s,
                "count": cnt,
                "last": t,
                "source": "Claude Code"
            })
    except Exception:
        pass
    return records


def load_qoder_usage(path):
    records = []
    if not os.path.isfile(path):
        return records
    try:
        data = json.load(open(path, encoding="utf-8"))
        for s, v in data.items():
            cnt = v.get("usageCount", 0)
            t = parse_ms(v.get("lastUsedAt"))
            records.append({
                "skill": s,
                "count": cnt,
                "last": t,
                "source": "Qoder"
            })
    except Exception:
        pass
    return records


def load_custom_usage(path):
    records = []
    if not os.path.isfile(path):
        return records
    try:
        # 尝试作为单 JSON 文件读取
        data = json.load(open(path, encoding="utf-8"))
        if isinstance(data, dict):
            usage = data.get("skillUsage", data)
            for s, v in usage.items():
                if isinstance(v, dict):
                    cnt = v.get("usageCount", 1)
                    t = parse_ms(v.get("lastUsedAt")) or parse_iso(v.get("ts", ""))
                else:
                    cnt = int(v) if str(v).isdigit() else 1
                    t = None
                records.append({"skill": s, "count": cnt, "last": t, "source": "Custom"})
            return records
    except Exception:
        pass

    # 作为 jsonl 读取
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        s = d.get("skill") or d.get("name")
        if not s:
            continue
        cnt = d.get("count", 1)
        t = parse_iso(d.get("ts", "")) or parse_ms(d.get("lastUsedAt"))
        records.append({"skill": s, "count": cnt, "last": t, "source": "Custom"})
    return records


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
    if not os.path.isdir(CATEGORIES):
        return out
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


def skill_matches(raw_skill, target_skill):
    """匹配技能名称：支持命名空间剥离 (xxx:name -> name) 及 gstack- 前缀兼容。"""
    if raw_skill == target_skill:
        return True
    base = raw_skill.split(":")[-1]
    if base == target_skill:
        return True
    raw_unprefixed = re.sub(r"^gstack-", "", base)
    target_unprefixed = re.sub(r"^gstack-", "", target_skill)
    if raw_unprefixed == target_unprefixed:
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description="AI 技能多端使用量统计与低频清理分析")
    ap.add_argument("--sort", choices=["count", "recent"], default="count",
                    help="排序方式: count=按调用次数降序(默认), recent=按最近使用时间降序")
    ap.add_argument("--top", type=int, default=20, help="展示使用最多的前 N 个技能（默认 20）")
    ap.add_argument("--days", type=int, default=90, help="最近 N 天未使用视为低频（默认 90）")
    ap.add_argument("--min", type=int, default=1, help="使用次数 < M 视为低频（默认 1，即零使用）")
    ap.add_argument("--sources", default="all",
                    help="指定数据源，逗号分隔 (all 或 claude,qoder,gstack)")
    ap.add_argument("--usage", default=None,
                    help="指定单个记录文件进行分析（将覆盖默认的多端自动加载）")
    ap.add_argument("--json", action="store_true", help="以 JSON 格式输出统计结果")
    ap.add_argument("--delete", action="store_true", help="实际删除低频技能目录（默认仅打印）")
    ap.add_argument("--dry-run", action="store_true", help="显式 dry-run（默认行为，仅打印）")
    args = ap.parse_args()

    records = []
    loaded_sources = []

    if args.usage:
        records = load_custom_usage(args.usage)
        loaded_sources.append(f"Custom ({args.usage})")
    else:
        srcs = [s.strip().lower() for s in args.sources.split(",")]
        load_all = "all" in srcs

        if (load_all or "claude" in srcs) and os.path.isfile(DEFAULT_CLAUDE):
            cr = load_claude_usage(DEFAULT_CLAUDE)
            if cr:
                records.extend(cr)
                loaded_sources.append(f"Claude Code ({DEFAULT_CLAUDE})")

        if (load_all or "qoder" in srcs) and os.path.isfile(DEFAULT_QODER):
            qr = load_qoder_usage(DEFAULT_QODER)
            if qr:
                records.extend(qr)
                loaded_sources.append(f"Qoder ({DEFAULT_QODER})")

        if (load_all or "gstack" in srcs) and os.path.isfile(DEFAULT_GSTACK):
            gr = load_gstack_usage(DEFAULT_GSTACK)
            if gr:
                records.extend(gr)
                loaded_sources.append(f"gstack ({DEFAULT_GSTACK})")

    desc = load_desc_zh()
    skills = scan_skills()
    now = datetime.now(timezone.utc)

    rows = []
    for cat, skill, path in skills:
        count = 0
        last_dt = None
        sources = set()

        for r in records:
            if skill_matches(r["skill"], skill):
                count += r["count"]
                if r["last"] and (last_dt is None or r["last"] > last_dt):
                    last_dt = r["last"]
                if r["source"]:
                    sources.add(r["source"])

        rows.append({
            "cat": cat,
            "skill": skill,
            "path": path,
            "count": count,
            "last": last_dt.isoformat() if last_dt else None,
            "last_dt": last_dt,
            "sources": sorted(list(sources)),
            "desc": desc.get((cat, skill), ""),
        })

    # 低频判定：次数 < min 或 最近使用早于 now - days
    cutoff = now - __import__("datetime").timedelta(days=args.days)

    def is_low(r):
        if r["count"] < args.min:
            return True
        if r["last_dt"] and r["last_dt"] < cutoff:
            return True
        return False

    low = [r for r in rows if is_low(r)]
    used = [r for r in rows if r["count"] > 0]

    # 排序
    if args.sort == "recent":
        # 最近使用时间倒序
        min_dt = datetime.min.replace(tzinfo=timezone.utc)
        used.sort(key=lambda r: (r["last_dt"] or min_dt, r["count"]), reverse=True)
    else:
        # 使用次数倒序
        min_dt = datetime.min.replace(tzinfo=timezone.utc)
        used.sort(key=lambda r: (r["count"], r["last_dt"] or min_dt), reverse=True)

    if args.json:
        # 清除无法直接序列化的 datetime 对象
        for r in rows:
            r.pop("last_dt", None)
        print(json.dumps({
            "total": len(rows),
            "used": len(used),
            "low_frequency_count": len(low),
            "sources_loaded": loaded_sources,
            "top_used": used,
            "low_frequency": low,
        }, ensure_ascii=False, indent=2))
        return

    print("==" * 35)
    print(f"【技能使用量统计报告】")
    print(f"技能总数: {len(rows)}  |  有使用记录: {len(used)}  |  低频候选: {len(low)}")
    print("加载数据源:")
    for s in loaded_sources:
        print(f"  • {s}")
    if not loaded_sources:
        print("  • （未找到可用数据源）")
    print("==" * 35)

    sort_label = "按最近使用时间倒序" if args.sort == "recent" else "按使用次数倒序"
    top_n = min(args.top, len(used))
    print(f"\nTOP {top_n} 活跃技能（{sort_label}）:")
    print("-" * 88)
    print(f" {'次数':>5} | {'最近使用时间':<16} | {'分类':<12} | {'技能名称':<30} | 来源")
    print("-" * 88)
    for r in used[:top_n]:
        dt_str = "--"
        if r["last_dt"]:
            dt_str = r["last_dt"].astimezone().strftime("%Y-%m-%d %H:%M")
        src_str = ", ".join(r["sources"]) if r["sources"] else "--"
        print(f" {r['count']:>5} | {dt_str:<16} | [{r['cat']:<10}] | {r['skill']:<30} | {src_str}")
    print("-" * 88)

    print(f"\n低频 / 零使用候选（共 {len(low)} 个，阈值: 次数<{args.min} 或 最近{args.days}天未用）:")
    for r in low[:15]:
        us = f"{r['count']}次" if r["count"] > 0 else "零使用"
        last = r["last_dt"].astimezone().strftime("%Y-%m-%d") if r["last_dt"] else "从未使用"
        print(f"  {us:<7} 最近:{last:<10} [{r['cat']}] {r['skill']}  {r['desc']}")
    if len(low) > 15:
        print(f"  ... 另有 {len(low) - 15} 个低频技能未在此处展开（使用 --json 或更严格阈值查看完整列表）")

    if args.delete:
        if args.dry_run:
            print("\n[dry-run] 未删除任何目录。去掉 --dry-run 或直接传 --delete 才会真正删除。")
            return
        print(f"\n⚠️  警告: 将删除 {len(low)} 个低频技能项:")
        for r in low:
            print(f"  rm -rf {r['path']}")
        try:
            confirm = input(f"\n确认删除上述 {len(low)} 项? 输入 yes 继续: ")
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
        print(f"已删除 {removed} 项。建议随后执行: python3 scripts/generate-skills-index.py && ./sync.sh")
    else:
        print("\n提示: 默认仅打印分析报告。如需清理低频技能，请运行: python3 scripts/analyze-skill-usage.py --delete")


if __name__ == "__main__":
    main()