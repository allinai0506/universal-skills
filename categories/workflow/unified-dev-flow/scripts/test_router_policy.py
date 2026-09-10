#!/usr/bin/env python3
"""Static policy contract: scoped prose, keyed tables and ordered resolution.

Whitespace is normalized. Alternatives is covered because its installed
dispatch advice can bypass policy. This is not a phase-two routing runtime.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
BASE = Path("categories/workflow/unified-dev-flow")
PATHS = {
    "skill": BASE / "SKILL.md",
    "policy": BASE / "references/policy-model.md",
    "enforcement": BASE / "references/enforcement.md",
    "alternatives": BASE / "references/alternatives.md",
    "map": Path("WORKFLOW-MAP.md"),
    "design": Path("docs/superpowers/specs/2026-09-10-unified-dev-flow-policy-router-design.md"),
}
RISKS = "auth permission security money data_integrity production state_machine concurrency migration".split()
TABLES = {
    "Proof Before Change": {
        "bug": ("failing test", "stable reproduction"),
        "feature": ("acceptance test", "not yet satisfied"),
        "refactor": ("passing characterization", "regression baseline before change"),
        "migration": ("dry-run", "forward", "rollback"),
        "performance": ("reproducible benchmark baseline",),
        "security": ("exploit/reproduction", "security assertion"),
        "config": ("schema", "lint", "configuration-load validation"),
        "ui": ("visual", "e2e acceptance evidence"),
    },
    "Complexity and Planning Depth": {
        "micro": ("entry gate file list", "compressed plan"),
        "small": ("brief implementation steps",),
        "medium": ("written spec, plan, and tasks", "one spec adapter"),
        "large": ("complete specification", "plan review", "task slices", "checkpoints"),
        "intractable": ("playbook", "audit trail", "human escalation"),
    },
    "Risk and Assurance Depth": {
        **{risk: ("at least adversarial proof",) for risk in RISKS
           if risk not in ("production", "migration")},
        "migration": ("dry-run", "forward", "rollback", "data_integrity", "adversarial"),
        "production": ("production-risk-review", "before s7", "other risks"),
    },
    "Capture Selection": {
        "research": ("select s8", "stop without delivery"),
        "intractable": ("select s8", "audit trail", "decision capture"),
        "large": ("full spec", "plan review", "slices", "checkpoints", "no automatic s8"),
        "unattended": ("may select s8", "show-me-your-work", "applicable"),
    },
    "Delivery Targets": {
        "patch": ("proposed patch only", "do not write the worktree"),
        "working_tree": ("modify and verify locally", "stop in the worktree"),
        "commit": ("local commit",), "pr": ("push", "pull request"),
        "merge": ("merge", "do not deploy"), "deploy": ("applicable production gates",),
    },
    "Controller Eligibility": {
        "delivery_target": ("ceiling at every stage", "never push, merge, or deploy above it"),
        "escalation": ("after three needs_fixes rounds", "does not reset"),
        "evidence": ("invalidate intersecting", "source or test changes", "reverify and re-review"),
        "spec_backend": ("selected adapter", "constitution restrictions", "slices", "convergence"),
    },
    "Review Selection": {
        "ordinary": ("health", "s4 baseline", "google-code-review"),
        "spec-bearing": ("code-review", "spec consistency"),
        "adversarial assurance/risk": ("interrogate", "risk specialists"),
        "independent reviewer unavailable": ("different-model/lab", "require interrogate", "fallback"),
        "cleanup evidence": ("ai-slop-cleaner --review", "only with actual cleanup/slop/refactor evidence",
                             "reviewer-only", "after a cleanup draft"),
    },
    "Intent Base Routes": {
        "bug": ("S0 → debug → S4 → S5 → S6 → S7(target)",),
        "feature": ("S0 → S1/S2/S3", "S4 → S5 → S6 → S7(target)"),
        "refactor": ("S0 → S3 → S4 → S5 → S6 → S7(target)",),
        "migration": ("S0 → S2/S3 → S4 → S5 → S6 → S7(target)",),
        "research": ("S1 → S3 → S8; stop without delivery",),
        "config": ("S6 as required by risk", "S7(target)"),
    },
}
SECTIONS = {
    "Resolution Order": ("r0 read-only recon → resume gate → entry gate → policy resolution",
                         "project-local optional index", "never initializes"),
    "Resume Semantics": ("fresh", "match", "compatible_drift", "conflicting_drift",
                         "goal fingerprint", "branch/worktree", "relevant diff"),
    "Policy Dimensions": ("complexity changes planning depth only", "risk selects assurance independently"),
    "Complexity and Planning Depth": ("before s4, insert the planning", "never selects assurance or adversarial reviewers"),
    "Risk and Assurance Depth": ("deterministic", "adversarial", "mutation", "real runner", "suitable core logic"),
    "Delivery Targets": ("default to working_tree", "higher target requires explicit user authorization",
                         "ceiling applies at every stage", "without writing artifacts",
                         "issue-tracker publication requires separate explicit authorization"),
    "Controller Roles": ("at most one controller", "controller-free routes", "explicit recorded handoff",
                         "local pstack swarm", "retired swarm alias"),
    "Controller Eligibility": (
        "before selecting or resuming", "inspect its installed native contract",
        "not eligible below commit unless the user explicitly selects full sdd and authorizes its required local commits",
        "selecting full sdd alone does not authorize the commits", "grants no push, merge, or deploy authority",
        "speckit-chain is only a candidate when a verified compatible adapter/handoff",
        "unconditional constitution rewrite", "one-shot implementation", "do not select the unadapted chain",
        "missing or unverified, reject", "compatible controller-free route", "never nest main loops"),
    "Spec Adapter Resolution": (
        "never maintain the same request concurrently", "unavailable, stop and report the mismatch",
        "do not silently switch a user's explicit choice or initialize tools"),
    "Unified Light Adapter": (
        "local specification artifact compatible with working_tree", "docs/specs/<task>.md", "name the path in the route",
        "medium requires spec/plan/tasks", "without writing it",
        "eligible only when issue-tracker publication is explicitly authorized",
        "tracker access plus triage labels are configured", "otherwise use the local artifact path"),
    "Spec Kit Adapter": (
        "initialized .specify/", "trimmable sequence",
        "ensure/read-only constitution → specify → clarify → plan → checklist → tasks → analyze → implement slices → converge",
        "read existing constitution by default",
        "create or update constitution only when missing or when the user explicitly changes project principles",
        "within delivery authorization", "large work uses slices and checkpoints", "unavailable required stages"),
    "OpenSpec Adapter": ("resolve the installed core or expanded profile", "target-project commands and configuration",
                         "do not hard-code command counts", "unknown or unavailable profile is a blocker"),
    "Proof Before Change": ("tdd remains the default implementation method for bugs and features",),
    "Review Selection": ("complexity alone never selects interrogate", "without editing reviewed source",
                         "health regression blocks", "codehealth-mcp", "explicit waiver"),
    "Capture Selection": ("patch keeps findings and the decision trail in the response",),
    "Scope Mapping": ("requested behavior", "root-cause dependency", "required test", "migration/build artifact",
                      "amend the entry gate before editing"),
    "Evidence Invalidation and Review Loop": ("source or test change invalidates intersecting",
                                             "s6 → s4 → s5 → s6", "after three needs_fixes review rounds, escalate to a human"),
}
PRECEDENCE = (
    ("resume", "safely resumable"), ("explicit user choice", "available"),
    ("project configuration",), ("sole initialized backend",),
    ("fail closed", "request ownership", "openspec/", ".specify/"),
    ("otherwise", "unified"),
)


def normalize(text: str) -> str:
    return " ".join(text.replace("`", "").replace("**", "").lower().split())


def sections(text: str) -> dict[str, str]:
    """Each heading owns only its body; another section cannot mask removal."""
    headings = list(re.finditer(r"^#{2,3} (.+)$", text, re.M))
    return {match[1]: text[match.end():headings[i + 1].start() if i + 1 < len(headings) else len(text)]
            for i, match in enumerate(headings)}


def rows(text: str) -> dict[str, str]:
    parsed = {}
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = [normalize(cell) for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and not re.fullmatch(r"[-: ]+", cells[0]):
                parsed[cells[0]] = " | ".join(cells[1:])
    return parsed


def validate(docs: dict[str, str]) -> list[str]:
    failures = []

    def require(label: str, body: str, phrases: tuple[str, ...]) -> None:
        for phrase in phrases:
            if normalize(phrase) not in normalize(body):
                failures.append(f"{label}: missing {phrase}")

    policy = sections(docs["policy"])
    for heading, phrases in SECTIONS.items():
        require(f"policy/{heading}", policy.get(heading, ""), phrases)
    for heading, expected in TABLES.items():
        actual = rows(policy.get(heading, ""))
        for key, phrases in expected.items():
            require(f"policy/{heading}/{key}", actual.get(key, ""), phrases)
            if heading == "Complexity and Planning Depth" and re.search(
                r"interrogate|adversarial|mutation|assurance", actual.get(key, "")
            ):
                failures.append(f"complexity/{key}: planning row must not select assurance/review")

    order = re.findall(r"^\d+\. (.*(?:\n[ \t]+.*)*)", policy.get("Spec Adapter Resolution", ""), re.M)
    if len(order) != len(PRECEDENCE):
        failures.append("adapter precedence: require six ordered resolution choices")
    for index, phrases in enumerate(PRECEDENCE):
        require(f"adapter precedence/{index + 1}", order[index] if index < len(order) else "", phrases)
    for document in ("policy", "design"):
        enum = re.search(r"^risk: \[([^]]+)\]$", docs[document], re.M)
        if not enum or [v.strip() for v in enum[1].split(",")] != RISKS:
            failures.append(f"{document}: canonical risk enum")

    skill = sections(docs["skill"])
    for heading, phrases in {
        "R0 Read-only Recon": ("without writing files", "never initialize"),
        "Resume Gate": ("progress.md", "match", "compatible_drift", "conflicting_drift"),
        "Entry Gate (first commitment after recon)": ("理解和假设", "最小方案 + 文件范围", "范围纪律", "验证计划", "proof_mode"),
        "Policy Resolution": ("policy-model.md", "before s4", "stage subset", "spec_backend", "proof_mode", "assurance_level", "delivery_target",
                              "bug + micro + security + production", "adversarial assurance"),
        "Controller Ownership Invariant": ("at most one controller", "never nest", "explicit persisted handoff",
                                           "controller eligibility", "three-round escalation", "evidence invalidation", "selected adapter"),
        "Spec Adapter Resolution": ("request ownership", "named local path", "authorized/configured issue publication", "installed profile"),
        "Evidence and Review Gates": ("health and google-code-review", "spec-bearing", "interrogate", "never complexity alone",
                                      "ai-slop-cleaner --review", "only for actual cleanup/slop/refactor evidence", "reviewer-only",
                                      "s6 → s4 → s5 → s6", "three needs_fixes", "invalidates intersecting"),
        "Delivery Limits": ("default implementation requests to working_tree", "higher targets require explicit authorization", "without artifacts"),
    }.items():
        require(f"skill/{heading}", skill.get(heading, ""), phrases)
    if docs["skill"].count("## Controller Ownership Invariant") != 1:
        failures.append("skill: one Controller Ownership Invariant")
    stages = rows(skill.get("Selected Stage Skills", ""))
    require("skill/S6", stages.get("s6 review", ""),
            ("health + google-code-review", "spec-bearing: code-review", "policy review selection"))
    require("skill/S8", stages.get("s8 capture", ""), ("policy capture selection",))
    if re.search(r"medium|large|intractable", stages.get("s6 review", "")):
        failures.append("skill/S6: complexity must not select reviewers")
    example = skill.get("Policy Resolution", "").split("Example:")[-1]
    if "S8" in example:
        failures.append("skill/large example: no automatic S8")

    for document, phrases in {
        "enforcement": ("R0 Read-only Recon", "proof_mode"),
        "alternatives": ("active static contract", "policy-model.md", "explicit persisted handoff",
                         "authorized local commits", "unadapted speckit-chain is ineligible",
                         "user explicitly changes project principles", "core/expanded", "never complexity alone",
                         "ai-slop-cleaner --review", "reviewer-only", "large does not automatically select s8",
                         "intractable requires audit trail/capture", "may select s8"),
        "map": ("Resume + Intent + Complexity + Risk + Domain + Delivery", "Fulfill delivery target",
                "按需创建或使用隔离 worktree", "state_machine", "Controller Eligibility", "不自动追加 S8",
                "复杂度本身不触发", "reviewer-only", "core 或 expanded", "docs/specs/<task>.md"),
    }.items():
        require(document, docs[document], phrases)
    risk_row = "auth / permission / security / money / data_integrity / state_machine / concurrency"
    require("map/risk row", rows(docs["map"]).get(risk_row, ""), ("至少 adversarial",))
    for document in ("skill", "policy", "alternatives", "map"):
        body = normalize(docs[document])
        for retired in ("scale decides depth", "large-feature one-shot", "merged, deployed",
                        "every diff-level mutant killed", "medium+: interrogate", "medium+ 必须 interrogate",
                        "medium+ mandatory", "large/intractable 必交", "missing or outdated governance"):
            if retired in body:
                failures.append(f"{document}: retired {retired}")
    return failures


def check_removal_sensitivity(docs: dict[str, str]) -> list[str]:
    """Prove whole-section/row deletions cannot hide behind global tokens."""
    failures = []
    policy = docs["policy"]
    for heading in SECTIONS:
        body = sections(policy)[heading]
        if not validate({**docs, "policy": policy.replace(body, "\n", 1)}):
            failures.append(f"checker accepted removed section: {heading}")
    for heading, expected in TABLES.items():
        body = sections(policy)[heading]
        for key in expected:
            line = next(line for line in body.splitlines()
                        if line.strip().startswith("|") and normalize(line.split("|")[1]) == key)
            if not validate({**docs, "policy": policy.replace(line, "", 1)}):
                failures.append(f"checker accepted removed row: {heading}/{key}")
    # Indented prose continuations may be unwrapped without changing meaning.
    reflowed = {name: re.sub(r"(?<!\n)\n[ \t]+(?=\S)", " ", text) for name, text in docs.items()}
    if validate(reflowed):
        failures.append("checker rejected harmless prose reflow")
    return failures


def main() -> int:
    try:
        docs = {name: (ROOT / path).read_text(encoding="utf-8") for name, path in PATHS.items()}
    except OSError as error:
        print(f"FAIL {error}")
        return 1
    failures = validate(docs)
    if not failures:
        failures = check_removal_sensitivity(docs)
    if failures:
        print("\n".join(f"FAIL {failure}" for failure in failures))
        return 1
    print("All router policy checks passed (including section/row deletion and prose reflow checks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
