---
name: clean-code-behavior-preserving-refactoring
description: Use when asked to refactor, clean up, simplify, extract, rename, reorganize, reduce duplication or nesting, delete over-engineered or dead code, or otherwise improve existing code without intentionally changing its externally observable behavior (重构, 清理代码, 精简, 优化结构). Do not use for feature development, intentional behavior changes, architectural/module-boundary redesign (use entropy-reduction), or rewrites without a separate specification.
---

# Purpose

Improve existing code so it is cleaner **and** smaller, without changing its externally observable behavior.

The central contract is:

> Make the code better and smaller, prove that behavior did not change.

Two biases drive every decision:

1. **Behavior before aesthetics** — a prettier implementation that changed behavior is a failed refactor.
2. **Delete-first** — the default move is removal. Keeping anything requires evidence: a test, a metric, or a business constraint.

This Skill turns refactoring into a constrained engineering loop rather than a subjective "make the code cleaner" exercise.

# When to Use

Use this Skill when the task is primarily one or more of:

- rename unclear identifiers;
- extract or split large functions;
- remove duplication;
- simplify control flow, flatten deep nesting;
- delete unused branches, parameters, abstractions, or dead code;
- consolidate repeated logic into a single source of truth;
- separate responsibilities inside an existing module/class;
- reorganize code while preserving behavior.

Typical request signals:

- "refactor this" / "重构一下";
- "clean up this code" / "清理这段代码";
- "this is too complex, I can't follow it";
- "too much nesting" / "嵌套太深";
- "there is duplicated logic" / "有重复逻辑";
- "break this function up";
- "simplify this class".

# When NOT to Use

Do not use this Skill as the primary method when:

- the requested behavior is intentionally changing;
- a new feature is being designed;
- the correct behavior is unknown;
- there are no meaningful acceptance criteria and the code has no reliable executable checks;
- the task is about where logic should live across modules, layer boundaries, or dependency direction — use **entropy-reduction** instead;
- the task requires a broad architectural migration rather than a localized refactor.

If a refactor exposes a necessary behavior change, stop treating that change as refactoring. Separate it into an explicit implementation task.

# Scope

- Scope type: Universal.
- Applies across languages and frameworks.
- Concrete test/build commands are project-specific.
- Existing project conventions override stylistic preferences from this Skill.
- Preserve public APIs, persistence formats, protocol behavior, error semantics, and side effects unless the task explicitly authorizes changes.

# Inputs and Ambiguity Gate

Before editing, establish:

1. The target files/modules.
2. The intended refactoring boundary.
3. Whether behavior is allowed to change (default: no).
4. Existing tests and the project's normal verification command.
5. Relevant public interfaces and observable behavior.
6. Repository-local instructions such as AGENTS.md, CLAUDE.md, RULES.md, or equivalent.

**Ambiguity gate:** if any of these cannot be established, stop before writing patches. Report what is missing and ask. Do not fill gaps with assumptions.

# Procedure

## 1. Establish the baseline

Inspect the target code and surrounding callers. Identify public entry points, inputs/outputs, exceptions, state mutations, I/O and external calls, invariants, and existing tests.

Run the narrowest relevant test suite before editing when practical. Record the baseline result.

If the baseline is already failing, distinguish pre-existing failures from failures introduced by the refactor.

## 2. State the refactoring invariant

Write a short internal statement:

> "I will improve structure X while preserving observable behavior Y."

Examples:

- extract validation logic while preserving validation outcomes;
- rename misleading variables without changing data flow;
- delete an unused parameter while preserving all real call sites' behavior.

Do not proceed with an ambiguous invariant.

## 3. Choose the smallest useful transformation

Prefer one small transformation at a time, in delete-first order:

1. delete dead code, unused parameters, speculative branches;
2. remove duplication (merge toward a single source of truth);
3. rename;
4. guard clauses / flatten conditionals;
5. extract method/function;
6. introduce a narrowly scoped abstraction — only if it removes real duplication, isolates a real responsibility, or clarifies a real contract;
7. reorganize related code.

Avoid combining unrelated cleanups in one change. Do not perform speculative redesign.

## 4. Make the change

Preserve every observable dimension of the contract — full checklist (ordering, null/empty handling, transaction boundaries, concurrency, serialization formats, …) in `references/refactoring-heuristics.md`.

Prefer names, small interfaces, and structure that reveal intent instead of comments that merely explain confusing code. Prefer immutability and local state over shared mutable state where the change is behavior-neutral.

## 5. Verify immediately

After each meaningful transformation:

- run the smallest relevant tests;
- run static analysis/format/lint checks when the project uses them;
- inspect the diff;
- check for accidental changes outside scope.

If a test fails, diagnose before acting: refactor-induced behavior change, pre-existing defect, test coupled to implementation details, or environment issue.

Do not "fix" a failing test merely to make the refactor pass unless the test itself is demonstrably incorrect.

## 6. Perform a final evidence pass

Verify before declaring success: intended behavior passes, no unrelated files changed, no dead code or compatibility shim left behind, the code is actually smaller or simpler (count if in doubt), and the diff is smaller than a rewrite would have been.

Use executable evidence where available.

# Output Protocol

Scale the report to the change size.

**Small change** (single function/module, few transformations): report the short evidence block from the Verification section.

**Large or multi-module change**: use the structured protocol:

```text
A. Inputs        — language/framework, goal priority, constraints, available tests, risk points
B. Plan          — ordered list of deletions/extractions/renames, each with expected gain and verification method
C. Patch         — final code only, per file
D. Verification  — minimal set of checks covering key paths and boundaries; note gaps if tests are insufficient
E. Risks         — top risks of this cleanup, each with a rollback strategy
Verdict          — [PASS] safe to merge, or [FAIL] with the exact missing verification items
```

Never end without the verdict. Never report "looks cleaner and should behave the same" as evidence — that is insufficient by definition.

# Rules

1. **Behavior before aesthetics.**
2. **Delete first.** Default to removing; keeping requires proof of value.
3. **Small reversible transformations** beat large rewrites.
4. **Tests are the safety net.** Without meaningful verification, mark the result `UNVERIFIED`.
5. **No abstraction without a demonstrated problem.**
6. **Names expose intent.** Avoid abbreviations and misleading generic names.
7. **One responsibility per function/class where practical** — split only when units become coherent and comprehension improves; never split mechanically.
8. **Minimize concepts, branches, and mutable state.** Guard clauses and early returns keep the main path straight.
9. **Small surface.** Reduce exposed interfaces and coupling; complexity belongs behind boundaries.
10. **Comments are not a substitute for structure** — but keep comments that explain non-obvious constraints or reasons code cannot express.
11. **Preserve project conventions** over personal preferences.
12. **Scope discipline.** No unrelated fixes, upgrades, formatting sweeps, or migrations mixed in.
13. **Evidence over confidence.** Report the checks actually performed, never equivalence-by-inspection.
14. **Let data shape drive code.** Adjusting data structures often deletes branching better than any control-flow trick.

# Rationalizations

| Excuse | Reality |
|---|---|
| "I inspected it carefully — behavior is identical" | Inspection is not execution. Run the narrowest relevant tests or mark `UNVERIFIED`. |
| "Tests are slow; skip them just this once" | One unverified change is how regressions ship. Run the smallest relevant subset. |
| "It's only a tiny cleanup" | Small changes still change behavior. Same protocol, smaller evidence block. |
| "I fixed that obvious bug while I was in there" | Scope creep invalidates the diff contract. Make it a separate task. |
| "This abstraction will pay off later" | Speculative. No abstraction without demonstrated duplication, responsibility, or contract. |
| "That failing test was probably flaky" | Diagnose before dismissing: behavior change, pre-existing defect, test coupling, or environment. |

# Red Flags — STOP

- You are about to write "should behave the same";
- verification is being skipped because of deadline pressure;
- an unrelated fix is sneaking into the diff;
- an abstraction is being extracted "for later";
- no baseline was recorded before the first edit.

All of these mean: return to the ambiguity gate or the verification step.

# Verification

Minimum verification:

1. Relevant tests pass.
2. Diff inspection shows only intended changes.
3. Static checks pass when configured by the repository.

Preferred evidence:

```text
Baseline tests: PASS
Refactored tests: PASS
Static checks: PASS
Diff scope: VERIFIED
Net effect: N lines removed / M branches reduced
Behavior preservation: VERIFIED
```

If any required evidence is unavailable:

```text
Status: UNVERIFIED
Reason: <specific missing evidence>
```

If tests fail after the change:

```text
Status: FAIL
Evidence: <test/check>
Likely cause: <behavior change / pre-existing failure / test issue / environment issue>
```

Do not conceal uncertainty.

# Failure / Escalation

Stop and escalate when:

- the intended behavior cannot be determined;
- public behavior is undocumented and tests are insufficient;
- a refactor requires changing an external contract;
- verification cannot distinguish a regression from an existing failure;
- the change expands into an architectural rewrite or module-boundary redesign (hand off to **entropy-reduction**);
- concurrency, persistence, security, or transaction semantics cannot be safely preserved.

Report what is known, what is uncertain, what evidence is missing, and the smallest next action required.

# Examples

- "Extract the validation logic from this 180-line method without changing behavior." → baseline tests → extract one coherent function → tests → diff inspection → evidence report.
- "这段代码太复杂了，嵌套太深，重复逻辑也多，帮我精简。" → ambiguity gate → baseline → delete dead weight first → merge duplicates → flatten nesting → verify each step → binary verdict.
- "Design a new validation architecture for the application." → not this Skill; route to entropy-reduction.
- "The code looks cleaner and should behave the same." → never acceptable as an outcome; it is not evidence.
