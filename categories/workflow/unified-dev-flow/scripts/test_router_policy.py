#!/usr/bin/env python3
"""Static acceptance checks for unified-dev-flow phase-one policy routing."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "categories/workflow/unified-dev-flow/SKILL.md"
POLICY = ROOT / "categories/workflow/unified-dev-flow/references/policy-model.md"
ENFORCEMENT = ROOT / "categories/workflow/unified-dev-flow/references/enforcement.md"
ALTERNATIVES = ROOT / "categories/workflow/unified-dev-flow/references/alternatives.md"
MAP = ROOT / "WORKFLOW-MAP.md"

FAILURES: list[str] = []


def read(path: Path) -> str:
    if not path.is_file():
        FAILURES.append(f"missing-file:{path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def require(name: str, text: str, needle: str) -> None:
    if needle not in text:
        FAILURES.append(f"missing:{name}:{needle}")


def forbid(name: str, text: str, needle: str) -> None:
    if needle in text:
        FAILURES.append(f"retired:{name}:{needle}")


def main() -> int:
    skill = read(SKILL)
    policy = read(POLICY)
    enforcement = read(ENFORCEMENT)
    alternatives = read(ALTERNATIVES)
    workflow_map = read(MAP)

    for needle in (
        "R0 Read-only Recon",
        "Resume before classification",
        "Intent selects the base route",
        "Complexity determines planning depth",
        "Risk determines assurance depth",
        "Controller Ownership Invariant",
        "Proof Before Change",
        "delivery_target",
        "S6 → S4 → S5 → S6",
        "Spec Adapter Resolution",
    ):
        require("skill", skill, needle)

    for needle in (
        "resume",
        "intent",
        "complexity",
        "risk",
        "domain",
        "delivery_target",
        "MATCH",
        "COMPATIBLE_DRIFT",
        "CONFLICTING_DRIFT",
        "deterministic",
        "adversarial",
        "mutation",
        "openspec/",
        ".specify/",
    ):
        require("policy", policy, needle)

    require("policy", policy, ".codegraph/")
    require("policy", policy, "project-local optional index")
    require("policy", policy, "controller-free routes are allowed")
    require("policy", policy, "`subagent-driven-development` (full SDD execution)")
    require("enforcement", enforcement, "R0 Read-only Recon")
    require("enforcement", enforcement, "proof_mode")
    require("alternatives", alternatives, "At most one selected Controller")
    require("alternatives", alternatives, "explicit persisted handoff")
    require("alternatives", alternatives, "selected Spec Adapter")
    require("alternatives", alternatives, "Constitution handling is ensure/read-only")
    require("alternatives", alternatives, "selected as the sole Controller")
    require("alternatives", alternatives, "the selected Controller owns repairs")
    require("map", workflow_map, "Resume + Intent + Complexity + Risk + Domain + Delivery")
    require("map", workflow_map, "Fulfill delivery target")
    require("map", workflow_map, "按需创建或使用隔离 worktree")
    require("skill", skill, "Before any\nS4, insert the planning required by complexity")
    require("skill", skill, "Large and intractable\nroutes also select S8 capture")
    require("skill", skill, "Example: **Feature + Large + Security + API + Working Tree**")

    for needle in (
        "Scale decides depth",
        "## Step 1 — Classify the task",
        "Large-feature one-shot",
        "Merged, deployed",
        "every diff-level mutant killed",
    ):
        forbid("skill", skill, needle)

    for needle in (
        "Stage alternatives (replace canonical only when the condition hits)",
        "**medium+ mandatory**",
        "no `.specify/` → Entry Gate §1 constraint docs act as constitution",
        "cycles inside the S6 loop",
        "`ultraqa` (fix-loop engine",
        "`executing-plans` (no-subagent env)",
        "`autopilot` / `ralph` +",
    ):
        forbid("alternatives", alternatives, needle)

    for needle in (
        "chooses exactly one controller",
        "Exactly one Controller owns execution",
        "controller: exactly one controller or none",
    ):
        forbid("policy", policy, needle)

    if skill.count("Controller Ownership Invariant") != 1:
        FAILURES.append("count:skill:Controller Ownership Invariant")

    if FAILURES:
        print("\n".join(f"FAIL {item}" for item in FAILURES))
        return 1
    print("All router policy checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
