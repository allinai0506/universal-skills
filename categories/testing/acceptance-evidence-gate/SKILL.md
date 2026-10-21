---
name: acceptance-evidence-gate
version: "2026.10.21-2"
synced-at: "2026-10-21T11:26:09"
description: "Gate a Coding Agent's 'done' or PR-ready claim on source-linked acceptance criteria, executed tests, current Git HEAD, and tamper-evident receipts. Use immediately before declaring a code change complete, fixed, or ready to merge - when the requirements are known but it is unclear whether they were actually proven at the current commit. Do not use for general code advice, exploratory analysis, or tasks with no identified acceptance criteria."
---

# Purpose

Prevent false completion claims. A coding change is **not verified complete** merely because code was written, compiled, or a developer/Agent says so. Decide whether the concrete, accepted requirements for a specific change have **current executable acceptance evidence**.

**This skill checks the completion claim; it does not plan, estimate, implement, or design tests for an entire project.**

# When to Use

- Immediately before saying a code change, bug fix, or PR is "done", "fixed", or "ready to merge".
- When a prior execution produced results but it is unclear whether tests were run for the **current** commit.
- When a user asks whether the claimed fix is actually verified against acceptance requirements.

# When NOT to Use

- Pure explanation, brainstorming, research, or a task with no software deliverable.
- A request to only review architecture; do not demand running a whole repository.
- When the task has no identified acceptance criteria: first request an acceptance contract; do not invent business requirements.
- When tests would require unsafe side effects, access to secrets, expensive infrastructure, or production mutations not explicitly authorized.
- Do not treat an automated gate pass as a replacement for security review, manual UX inspection, or reviewer approval where these are required.

# Scope

`Universal`: works on Git repositories with tests runnable as command arrays. Python 3.9+ and Git are **tools required to execute this package**, not a restriction on application language/framework. **Gate requires a clean committed HEAD**: it is designed for final verification, not uncommitted in-progress work.

# Inputs

1. `repo`: local, trusted Git working-tree root, at the commit to be assessed.
2. `acceptance contract`: JSON file based on `assets/contract.template.json`, approved acceptance criteria with `source`, `source_ref`, and check IDs.
3. Test/check commands installed and executable in the local repo, plus any access required to run them safely.
4. An output directory **outside** the repository to store logs and `receipt.json`.

Read `references/verification-rules.md` when constructing the acceptance contract or interpreting a pass. Read `references/source-map.md` only if provenance is requested.

# Procedure

1. **Define completion before checking:** identify the task's accepted requirements from the user/issue/approved spec. Write one criterion per observable behavior, with source reference. Do not silently revise criteria to match implemented code.
2. **Map each criterion to at least one executable acceptance check** (`kind: "acceptance"`). Review command arrays. Ensure the check actually exercises the behavior and assertively fails when behavior is wrong. No `echo`, `true`, mock-only, or vacuous checks count as acceptance evidence.
3. **Verify readiness:** ensure the code and relevant tests are committed; inspect `git status`, branch/HEAD, permissions and side effects. Do not skip permissions or force-clean the worktree.
4. **Execute (at the repo's current committed state):**

   ```bash
   python3 scripts/acceptance_gate.py run \
     --repo /path/to/repo \
     --contract /path/to/contract.json \
     --out /tmp/acceptance-evidence-unique-run
   ```

   The command returns `0` only if all configured checks return zero, do not time out, and the repo remains at the same clean HEAD. Logs and a JSON receipt are captured even if a check fails.

5. **Validate the receipt** (same repo, unchanged contract, same clean HEAD, recent logs):

   ```bash
   python3 scripts/acceptance_gate.py verify \
     --repo /path/to/repo \
     --contract /path/to/contract.json \
     --receipt /tmp/acceptance-evidence-unique-run/receipt.json
   ```

   When the claim must survive an adversarial reader, **anchor** the receipt —
   register its digest in a file the claiming Agent cannot write, and verify
   against it:

   ```bash
   python3 scripts/acceptance_gate.py anchor \
     --repo /path/to/repo \
     --receipt /tmp/acceptance-evidence-unique-run/receipt.json \
     --anchor <protected-location>/evidence.json

   python3 scripts/acceptance_gate.py verify \
     --repo /path/to/repo \
     --contract /path/to/contract.json \
     --receipt /tmp/acceptance-evidence-unique-run/receipt.json \
     --anchor <protected-location>/evidence.json
   ```

   The anchor is write-once and binds the work item, the HEAD and the receipt
   digest. Without an anchor, a forger who can rewrite the receipt can also
   recompute its digest; with one, forging requires an anchor the Agent cannot
   write. See `references/verification-rules.md` for where an anchor belongs.

6. **Review semantic coverage manually:** confirm the acceptance commands genuinely test each agreed criterion, including negative/boundary behavior when relevant. Mechanical receipt validation does not prove that test assertions are adequate or that the specification is correct.
7. **Report** using `assets/completion-report.template.md` with exact HEAD, acceptance IDs, commands, results, receipt path, and unresolved risks. State `VERIFIED` **only** if both the automated gate and the semantic coverage check pass. Otherwise report `UNVERIFIED` or `BLOCKED`, with reasons.

# Rules

- Evidence first: claims must be traceable to the executed command, exit status, log, criterion and commit.
- Never present generated tests as independent external acceptance criteria. Contract source must come from the user, issue, or an explicitly approved specification.
- Never call tests successful based only on old CI screenshots, an Agent's narrative, or `git diff`.
- Changes to contract, Git HEAD, tracked files, logs, or the receipt itself invalidate a prior receipt. Re-run as needed.
- Run configured commands **without shell expansion**. Review them before execution; the script does not sandbox or guarantee safety of the commands.
- No automatic installation, cleanup, committing, pushing, or use of remote services.
- `PASS` from the script is a **necessary** completion gate, not sufficient proof of business correctness.
- The receipt digest detects **accidental** post-run edits; it does not stop a determined forger, because the claiming Agent can rewrite the receipt and recompute the digest. For claims that must survive an adversarial reader, use `anchor` to commit the receipt digest in a file the Agent cannot write, and verify with `--anchor`. See `references/verification-rules.md` for where an anchor belongs and what still remains outside its reach.

# Verification

- The `verify` CLI exits with `0` only if: contract digest matches, receipt digest matches (no post-run edit), current repository is clean and at the captured HEAD, receipt age is within allowed limit, each expected check has a zero exit, and all log digests match. With `--anchor`, the anchor must additionally commit to this receipt's digest, the work item and the current HEAD.
- Each acceptance criterion has one or more mapped passing check IDs; mapping and actual behavioral coverage must still be inspected by the Agent.
- The package self-tests with:

  ```bash
  python3 -m unittest discover -s scripts -p 'test_*.py' -v
  ```

- See `references/verification-rules.md` for pass/fail semantics, anchoring, and trust boundaries.

# Failure / Escalation

- No accepted requirements, unclear expected behavior, or missing test environment: `UNVERIFIED`, name missing input and ask for it. Do **not** create a self-serving acceptance contract.
- Test failed, timed out, output changed, or Git state drifted: `BLOCKED` with the specific check/log and commit. Do not claim done or bypass.
- No safe way to exercise the acceptance behavior (e.g. production-only dependency): `UNVERIFIED`, propose a safe validation plan and request authorization before running tests.
- Gate passes but behavioral coverage is weak: `UNVERIFIED` with the uncovered criterion and proposed test addition.

# Examples

**Valid:** A committed bug fix has a user-approved criterion with a failing-before/fixed-after regression test, and `verify` passes on the exact new HEAD. Report `VERIFIED`, cite receipt and known limitations.

**Invalid:** "Fixed the wide XLSX→PDF truncation bug" with only a green build check, no wide-sheet PDF content acceptance assertions. Even if the build passes, report `UNVERIFIED` and explain the missing evidence.

**Invalid:** Tests passed at HEAD A, a later commit B modifies behavior. `verify` on B must fail; rerun against B.
