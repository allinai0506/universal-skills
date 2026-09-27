#!/usr/bin/env python3
"""Deterministically validate Semantic Domain Modeling artifacts.

No third-party dependencies are required.
"""

from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

CORE_SECTIONS = {
    "glossary": ("glossary", "术语"),
    "objects": ("objects", "对象"),
    "relationships": ("relationships", "关系"),
    "states": ("states", "状态"),
    "actions": ("actions", "动作"),
    "invariants": ("invariants", "不变量"),
    "sources of truth": ("sources of truth", "source of truth", "事实源", "权威来源"),
}

BROWNFIELD_SECTIONS = {
    "evidence inventory": ("evidence inventory", "证据清单", "证据盘点"),
    "semantic inventory": ("semantic inventory", "语义清单", "语义盘点"),
    "intended model": ("intended model", "意图模型", "预期模型"),
    "implemented model": ("implemented model", "实现模型"),
    "observed behavior": ("observed behavior", "观察行为", "实际行为"),
    "as-is model": ("as-is model", "现状模型"),
    "to-be model": ("to-be model", "目标模型"),
    "discovery gate": ("discovery gate", "考古门禁", "发现门禁"),
}

PLACEHOLDER_PATTERNS = [
    r"<term>", r"<meaning>", r"<objectname>", r"<invariant", r"<source>",
    r"<bounded scope", r"<date / commit", r"<fact>", r"<ambiguity>", r"<evidence>",
    r"<concept>", r"<problem>", r"<target>", r"<scope>",
]


def headings(text: str) -> list[str]:
    return [m.group(1).strip().lower() for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, re.MULTILINE)]


def section_present(all_headings: list[str], aliases: tuple[str, ...]) -> bool:
    return any(any(alias in h for alias in aliases) for h in all_headings)


def inferred_mode(text: str) -> str:
    if re.search(r"Mode:\s*BROWNFIELD", text, re.IGNORECASE):
        return "brownfield"
    hs = headings(text)
    if section_present(hs, BROWNFIELD_SECTIONS["as-is model"]) or section_present(hs, BROWNFIELD_SECTIONS["semantic inventory"]):
        return "brownfield"
    return "greenfield"


def validate(path: Path, mode: str = "auto") -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"file not found: {path}"]
    text = path.read_text(encoding="utf-8")
    actual_mode = inferred_mode(text) if mode == "auto" else mode

    minimum = 900 if actual_mode == "brownfield" else 500
    if len(text.strip()) < minimum:
        errors.append(f"domain model is too small to be a meaningful {actual_mode} artifact (<{minimum} chars)")

    hs = headings(text)
    for label, aliases in CORE_SECTIONS.items():
        if not section_present(hs, aliases):
            errors.append(f"missing required section: {label}")

    if actual_mode == "brownfield":
        for label, aliases in BROWNFIELD_SECTIONS.items():
            if not section_present(hs, aliases):
                errors.append(f"missing brownfield section: {label}")
        for token in ("Intended", "Implemented", "Observed"):
            if token.lower() not in text.lower():
                errors.append(f"brownfield model must distinguish {token} evidence/model")
        if "READ_ONLY" not in text and "READ-ONLY" not in text:
            errors.append("brownfield model must state READ_ONLY/READ-ONLY discovery rule")

    lowered = text.lower()
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, lowered):
            errors.append(f"unresolved template placeholder detected: {pattern}")

    if not re.search(r"AUTHORITATIVE|权威", text, re.IGNORECASE):
        errors.append("sources of truth must identify at least one AUTHORITATIVE/权威 source")

    invariant_matches = re.findall(
        r"^#{1,6}\s+.*(?:invariants|不变量).*$([\s\S]*?)(?=^#{1,6}\s+|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if invariant_matches and not any(re.search(r"(^|\n)\s*(?:[-*]|\d+[.)])\s+\S", body) for body in invariant_matches):
        errors.append("invariants section must contain at least one explicit invariant item")

    return errors


def validate_brownfield_bundle(domain_model: Path) -> list[str]:
    errors = validate(domain_model, "brownfield")
    docs = domain_model.parent
    companions = {
        "semantic conflicts": docs / "semantic-conflicts.md",
        "source of truth": docs / "source-of-truth.md",
        "semantic migration plan": docs / "semantic-migration-plan.md",
    }
    for label, path in companions.items():
        if not path.exists():
            errors.append(f"missing brownfield companion artifact: {label} ({path.name})")
        elif len(path.read_text(encoding="utf-8").strip()) < 180:
            errors.append(f"brownfield companion artifact is too small: {path.name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate semantic domain modeling artifacts")
    parser.add_argument("path", help="Path to docs/domain-model.md")
    parser.add_argument("--mode", choices=("auto", "greenfield", "brownfield"), default="auto")
    parser.add_argument("--bundle", action="store_true", help="For brownfield, require companion docs in the same docs directory")
    args = parser.parse_args()
    path = Path(args.path).expanduser().resolve()

    if args.bundle:
        errors = validate_brownfield_bundle(path)
    else:
        errors = validate(path, args.mode)

    if errors:
        print("FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print("PASS")
    print(f"Validated: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
