# Unified Dev Flow Task Execution Kernel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the phase-two stdlib-only Task Execution Kernel defined by `docs/superpowers/specs/2026-09-11-unified-dev-flow-runtime-design.md`.

**Architecture:** Phase One supplies an immutable resolved `RouteContract`. The Kernel accepts strict commands, returns `Decision(events, outcome)`, appends request-aware `EventBatch` records, and derives all state through one pure Reducer. Providers observe workspaces or run registered verification commands; they never own workflow state.

**Tech Stack:** Python 3.11+ standard library, `unittest`, JSON/JSONL, `fcntl` on supported Unix hosts, Git CLI only inside `TrustedLocalVerifier` observation.

## Global Constraints

- Implement a Task Execution Kernel, not a generic workflow engine; do not add stage, waiver, cleanup, resume-probe, doctor, service, UI, Codex, Herdr, worktree, or Agent integration.
- Use Python standard library only; reject unknown schema fields and versions fail closed.
- `events.jsonl` contains all Gate-semantic data and is replayed directly; do not add `run.json` or `tasks.json` snapshots.
- Reducer is the only state-transition authority; Gate returns events plus an allowed/denied outcome, never `new_state`.
- Every mutating command carries `request_id`; side-effecting verification persists `REQUEST_RESERVED` before execution and `REQUEST_RESOLVED` after it. Never claim exactly-once external side effects.
- `delivery_target: patch` cannot initialize runtime. Delivery ordering is `patch < working_tree < commit < pr < merge < deploy`.
- Evidence, review, acceptance, and delivery are bound to current task/input/verdict fingerprints. Old delivery assertions cannot satisfy a newly accepted revision.
- `scope_origin` is immutable within one `task_revision`, including NEEDS_FIXES retries. An unresolved scope violation blocks a new origin.
- `.unified-dev-flow/**` and `.git/**` are excluded from business fingerprints; runtime never creates `.codegraph/` and never writes `.omc/` or `.superpowers/sdd/` as product behavior.
- `TrustedLocalVerifier` is explicitly trusted, not a sandbox. It runs only registered argv with `shell=False`, bounded cwd/time/output, and makes no network/filesystem isolation claim.
- Tests use real files and subprocesses where observable behavior matters. Each production change follows RED → GREEN and records both outputs in the task report.
- Each task commit contains only its planned product/test files. Preserve unrelated `.omc/` state.

## File Map

- `scripts/unified_workflow/model.py`: strict schema parsing, canonical JSON, identifiers, paths, Route/Task/Workspace/Evidence/Review value objects.
- `scripts/unified_workflow/commands.py`: Command and Decision/Outcome types.
- `scripts/unified_workflow/events.py`: domain event and hashed EventBatch serialization.
- `scripts/unified_workflow/reducer.py`: pure event replay into RunState/TaskState/request lifecycle.
- `scripts/unified_workflow/gate_kernel.py`: command validation, freshness, dependency, scope, review, escalation, and delivery decisions.
- `scripts/unified_workflow/store.py`: run layout, Unix lock, append/fsync, replay integrity, reservation, blob publication, and in-doubt handling.
- `scripts/unified_workflow/providers/`: Provider protocol, deterministic mock, trusted local observation and command execution.
- `scripts/unified_workflow/cli.py` and `scripts/unified-workflow`: thin command surface and stable exit codes.
- `scripts/test_unified_workflow_*.py`: executable stdlib test files, each with `main()`/`unittest.main()` and direct-run support.

---

### Task 1: Strict Models, Canonical Data, and Path Safety

**Files:**
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/__init__.py`
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/model.py`
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/commands.py`
- Create: `categories/workflow/unified-dev-flow/scripts/test_unified_workflow_model.py`

**Interfaces:**
- Produces: `ValidationError(code, message)`, `canonical_json(value) -> str`, `canonical_sha256(value) -> str`, `validate_id(value, field) -> str`, `resolve_project_path(root, value, field) -> Path`.
- Produces immutable dataclasses: `RouteObligations`, `RouteContract`, `WriteScope`, `VerificationCommand`, `TaskContract`, `WorkspaceRevision`, `EvidenceRecord`, `ReviewAssertion`, `Command`, `Allowed`, `Denied`, `Decision`.
- Every `from_dict()` rejects missing/unknown fields, booleans used as integers, unknown enums, invalid IDs, duplicate list values, and invalid relative paths.

- [ ] **Step 1: Write focused failing model tests**

Create tests that hand-build literal dictionaries and cover these observable breaks:

```python
class StrictModelTests(unittest.TestCase):
    def test_route_contract_rejects_unknown_field(self):
        raw = valid_route()
        raw["surprise"] = True
        with self.assertRaisesRegex(ValidationError, "UNKNOWN_FIELD"):
            RouteContract.from_dict(raw)

    def test_patch_route_is_valid_data_but_runtime_ineligible(self):
        raw = valid_route()
        raw["delivery_target"] = "patch"
        route = RouteContract.from_dict(raw)
        self.assertEqual(route.delivery_target, "patch")

    def test_task_rejects_control_directory_write(self):
        raw = valid_task()
        raw["write_scope"]["allowed_paths"] = [".unified-dev-flow/**"]
        with self.assertRaisesRegex(ValidationError, "CONTROL_PATH"):
            TaskContract.from_dict(raw)

    def test_resolved_path_rejects_symlink_escape(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (self.root / "link").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValidationError, "PATH_ESCAPE"):
            resolve_project_path(self.root, "link/file", "cwd")

    def test_canonical_hash_is_key_order_independent(self):
        self.assertEqual(canonical_sha256({"b": 2, "a": 1}),
                         canonical_sha256({"a": 1, "b": 2}))
```

- [ ] **Step 2: Run RED**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_model.py`

Expected: fail because `unified_workflow.model` and `unified_workflow.commands` do not exist.

- [ ] **Step 3: Implement strict value objects**

Use frozen dataclasses and explicit parsers. The Route schema must include the exact phase-one axes plus:

```python
DELIVERY_ORDER = ("patch", "working_tree", "commit", "pr", "merge", "deploy")
OUTCOMES = ("success", "denied", "provider_failure", "abandoned")
VERDICTS = ("MERGE_READY", "NEEDS_FIXES", "ESCALATE")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CONTROL_PREFIXES = (".git", ".unified-dev-flow")
```

`Command` fields are `schema_version, request_id, command_type, work_id, task_id, actor, expected_sequence, payload`; `Decision` fields are `events, outcome`. Keep actor/payload as recursively JSON-safe mappings copied into immutable plain data.

- [ ] **Step 4: Run GREEN and mutation counter-cases**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_model.py`

Expected: all tests pass. Confirm tests fail if unknown-field rejection, canonical sorting, or resolved containment check is removed.

- [ ] **Step 5: Commit**

```bash
git add categories/workflow/unified-dev-flow/scripts/unified_workflow \
  categories/workflow/unified-dev-flow/scripts/test_unified_workflow_model.py
git commit -m "feat: add unified workflow protocol models"
```

---

### Task 2: Event Batches, Request Lifecycle, and Pure Reducer

**Files:**
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/events.py`
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/reducer.py`
- Create: `categories/workflow/unified-dev-flow/scripts/test_unified_workflow_reducer.py`

**Interfaces:**
- Consumes: canonical helpers and model dataclasses from Task 1.
- Produces: `DomainEvent`, `EventBatch.create(...)`, `EventBatch.from_dict(...)`, `verify_batch(previous, batch)`.
- Produces: `RunState`, `TaskState`, `RequestState`, `initial_state()`, `reduce_event(state, event)`, `replay(batches)`.
- `replay` verifies schema, continuous sequence, previous hash and batch hash before applying events.

- [ ] **Step 1: Write reducer and integrity tests first**

Cover literal event histories:

```python
def test_replay_rejects_broken_hash_chain(self):
    first = make_batch(1, ZERO_HASH, [run_created_event()])
    second = make_batch(2, first.batch_hash, [task_added_event()])
    raw = second.to_dict()
    raw["previous_hash"] = "sha256:" + "f" * 64
    with self.assertRaisesRegex(IntegrityError, "EVENT_HASH_MISMATCH"):
        replay([first, EventBatch.from_dict(raw)])

def test_request_without_resolution_is_in_doubt(self):
    state = replay([reserved_batch("req-1")])
    self.assertEqual(state.requests["req-1"].status, "in_doubt")

def test_invalidation_reopens_acceptance_as_stale(self):
    state = replay(accepted_history() + [batch("TASK_INVALIDATED", {"task_id": "a", "new_task_revision": 2})])
    self.assertEqual(state.tasks["a"].status, "stale")
    self.assertFalse(state.tasks["a"].currently_satisfied)
```

Also cover: duplicate/conflicting request resolution, all Task transitions, third-round counters per task, dependency satisfaction, current acceptance fingerprints, delivery assertion storage, and deterministic replay equality.

- [ ] **Step 2: Run RED**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_reducer.py`

Expected: fail because event/reducer modules do not exist.

- [ ] **Step 3: Implement EventBatch and Reducer**

Each JSONL record represents one batch and uses `sequence` per batch. `batch_hash` is SHA-256 over the canonical batch dictionary without `batch_hash`. `REQUEST_RESERVED` creates `in_doubt`; `REQUEST_RESOLVED` stores its stable outcome. Reducer returns new immutable state and never reads files, time, Git, or Provider data.

`TASK_INVALIDATED` sets the named task and transitive dependents to `stale`, clears current acceptance bindings, increments only explicitly named `new_task_revision`, and preserves history. `TASK_NEEDS_FIXES` increments that task's review round without changing `scope_origin`.

- [ ] **Step 4: Run GREEN**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_reducer.py`

Expected: all reducer/integrity tests pass with no warnings.

- [ ] **Step 5: Commit**

```bash
git add categories/workflow/unified-dev-flow/scripts/unified_workflow/events.py \
  categories/workflow/unified-dev-flow/scripts/unified_workflow/reducer.py \
  categories/workflow/unified-dev-flow/scripts/test_unified_workflow_reducer.py
git commit -m "feat: add event replay and workflow reducer"
```

---

### Task 3: Gate Kernel and Freshness Rules

**Files:**
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/gate_kernel.py`
- Create: `categories/workflow/unified-dev-flow/scripts/test_unified_workflow_gate.py`

**Interfaces:**
- Consumes: `RunState`, `Command`, `RouteContract`, and optional current `WorkspaceRevision`/provider result.
- Produces: `decide(state, command, observed_facts=None) -> Decision`.
- Supported command types: `ADD_TASK`, `READY_TASK`, `START_TASK`, `REPORT_TASK`, `RECORD_VERIFICATION`, `WAIT_FOR_REVIEW`, `RECORD_REVIEW`, `ACCEPT_TASK`, `RESOLVE_BLOCKER`, `RECORD_DELIVERY`, `COMPLETE_RUN`, `CANCEL_TASK`, `CANCEL_RUN`.

- [ ] **Step 1: Write transition-matrix tests first**

Use real model instances and literal expected event names. Required counter-cases include:

```python
def test_denied_completion_persists_input_invalidation(self):
    state = accepted_run(input_fingerprint="sha256:old")
    decision = decide(state, complete_command(), workspace("sha256:new"))
    self.assertIsInstance(decision.outcome, Denied)
    self.assertEqual([e.event_type for e in decision.events], ["TASK_INVALIDATED"])

def test_third_needs_fixes_is_one_escalation_batch(self):
    decision = decide(waiting_review_state(review_round=2), needs_fixes_command())
    self.assertEqual(
        [e.event_type for e in decision.events],
        ["REVIEW_RECORDED", "TASK_INVALIDATED", "TASK_BLOCKED", "RUN_BLOCKED", "ESCALATE_TO_HUMAN"],
    )

def test_delivery_must_bind_current_acceptance_set(self):
    decision = decide(accepted_run(), delivery_command(acceptance_set_sha256="sha256:old"))
    self.assertEqual(decision.outcome.reason_code, "EVIDENCE_STALE")
```

Also test: patch init denial; dependency checks at ready and start; one running writable task; immutable scope origin across retries; unresolved scope violation; required verification claim union; allowed review provenance; verification success/failure; cascading stale tasks; every delivery ceiling pair; required/optional/cancelled completion; all stable reason codes.

- [ ] **Step 2: Run RED**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_gate.py`

Expected: fail because `gate_kernel.decide` does not exist.

- [ ] **Step 3: Implement the pure Gate**

Use a command-handler mapping, one function per command type. Shared helpers must be limited to exact invariants: `fresh_evidence`, `fresh_review`, `acceptance_set_sha256`, `dependency_closure`, `scope_violations`, and `delivery_at_or_below_ceiling`.

Denied decisions may contain fact events such as `TASK_INVALIDATED`, `SCOPE_VIOLATION`, or failed `VERIFICATION_RECORDED`; they must never contain the denied target transition. Gate does not create request lifecycle events—that is Store protocol responsibility.

- [ ] **Step 4: Run GREEN and transition mutation checks**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_gate.py`

Expected: all Gate tests pass. Confirm at least one test fails when dependency recheck, provenance check, acceptance-set binding, or review-limit comparison is inverted.

- [ ] **Step 5: Commit**

```bash
git add categories/workflow/unified-dev-flow/scripts/unified_workflow/gate_kernel.py \
  categories/workflow/unified-dev-flow/scripts/test_unified_workflow_gate.py
git commit -m "feat: enforce unified workflow gates"
```

---

### Task 4: Durable Store, Locking, Reservations, and Evidence Blobs

**Files:**
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/store.py`
- Create: `categories/workflow/unified-dev-flow/scripts/test_unified_workflow_store.py`

**Interfaces:**
- Produces: `RunStore(project_root: Path, work_id: str)`, `load() -> RunState`, `execute(command, facts=None) -> CommandResult`, `execute_verification(command, provider) -> CommandResult`, `publish_blob(data: bytes) -> BlobReference`.
- Store owns `REQUEST_RESERVED`/`REQUEST_RESOLVED`; Gate owns only domain decisions.
- `CommandResult` exposes `outcome`, derived `state`, and diagnostic warnings.

- [ ] **Step 1: Write filesystem and crash-boundary tests first**

Use `TemporaryDirectory` and real files. Cover:

```python
def test_retry_returns_prior_outcome_without_calling_provider_twice(self):
    provider = CountingProvider(success_result())
    first = self.store.execute_verification(verify_command("req-1"), provider)
    second = self.store.execute_verification(verify_command("req-1"), provider)
    self.assertEqual(first.outcome, second.outcome)
    self.assertEqual(provider.calls, 1)

def test_reserved_request_without_resolution_is_in_doubt(self):
    self.store.append_test_batch(request_reserved_event("req-1"))
    result = self.store.execute_verification(verify_command("req-1"), CountingProvider(success_result()))
    self.assertEqual(result.outcome.reason_code, "REQUEST_IN_DOUBT")

def test_missing_optional_blob_warns_but_replays(self):
    result = self.store.load()
    self.assertTrue(result.tasks)
    self.assertIn("MISSING_DIAGNOSTIC_BLOB", self.store.diagnostics)
```

Also test: lock contention returns `LOCK_BUSY`; sequence race returns `EXPECTED_SEQUENCE_MISMATCH`; truncated JSON/hash/schema corruption fail closed; same request/different payload conflicts; blob temp+fsync+rename and digest mismatch warning; directory/file modes; symlinked control directory rejection; no snapshot files.

- [ ] **Step 2: Run RED**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_store.py`

Expected: fail because `RunStore` does not exist.

- [ ] **Step 3: Implement Store protocol**

Use `fcntl.flock(..., LOCK_EX | LOCK_NB)` and keep the writer lock through side-effecting verification. Append exactly one canonical JSON line per EventBatch, then flush and `os.fsync`. For verification: append/fsync reservation batch, observe pre revision, run provider, observe post revision, publish blobs, observe commit revision, decide, then append/fsync decision events plus resolution.

If the process dies after reservation, replay yields `in_doubt`; retry never reruns it. `resolve_request(request_id, outcome, actor, note)` appends an audited resolution. Diagnostic blob absence never changes RunState.

- [ ] **Step 4: Run GREEN**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_store.py`

Expected: all store tests pass with deterministic temporary-directory cleanup.

- [ ] **Step 5: Commit**

```bash
git add categories/workflow/unified-dev-flow/scripts/unified_workflow/store.py \
  categories/workflow/unified-dev-flow/scripts/test_unified_workflow_store.py
git commit -m "feat: persist unified workflow event batches"
```

---

### Task 5: MockProvider and TrustedLocalVerifier

**Files:**
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/providers/__init__.py`
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/providers/base.py`
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/providers/mock.py`
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/providers/trusted_local.py`
- Create: `categories/workflow/unified-dev-flow/scripts/test_unified_workflow_providers.py`

**Interfaces:**
- Produces Protocol methods `observe_workspace(request) -> WorkspaceRevision` and `run_verification(request) -> VerificationResult`.
- Produces deterministic `MockProvider(observations, results)` with FIFO fixture consumption.
- Produces `TrustedLocalVerifier(project_root, task_contract, environment=None)`; `run_verification(command_id)` resolves only a registered command.

- [ ] **Step 1: Write provider behavior tests first**

Use a real temporary Git repository and a real child Python process:

```python
def test_local_verifier_rejects_unregistered_command(self):
    with self.assertRaisesRegex(ProviderError, "COMMAND_NOT_REGISTERED"):
        self.provider.run_verification("not-registered")

def test_local_verifier_truncates_output_but_hashes_full_stream(self):
    result = self.provider.run_verification("large-output")
    self.assertTrue(result.output_truncated)
    self.assertEqual(len(result.stdout), self.limit)
    self.assertEqual(result.stdout_sha256, hashlib.sha256(self.full_output).hexdigest())

def test_runtime_directory_does_not_change_business_revision(self):
    before = self.provider.observe_workspace(request_for(["**/*"]))
    write_runtime_file(self.root)
    after = self.provider.observe_workspace(request_for(["**/*"]))
    self.assertEqual(before.verification_input_fingerprint, after.verification_input_fingerprint)
```

Also cover timeout, nonzero exit, cwd escape, minimal environment, tracked/untracked content changes, `.git/**` exclusion, changed path reporting, and MockProvider exhaustion/errors.

- [ ] **Step 2: Run RED**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_providers.py`

Expected: fail because provider modules do not exist.

- [ ] **Step 3: Implement providers**

Use `subprocess.Popen(argv, shell=False, cwd=resolved_cwd, env=minimal_env)` with timeout handling and bounded captured bytes. Hash full stdout/stderr incrementally even when retained output is truncated. Workspace fingerprint walks relevant real files in sorted POSIX path order, rejects symlink escapes, excludes `.git` and `.unified-dev-flow`, and includes Git HEAD/diff metadata only as optional details.

Module/class docstrings must say TrustedLocalVerifier has caller-equivalent authority and is not a sandbox.

- [ ] **Step 4: Run GREEN**

Run: `python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_providers.py`

Expected: all provider tests pass; no child process remains after timeout.

- [ ] **Step 5: Commit**

```bash
git add categories/workflow/unified-dev-flow/scripts/unified_workflow/providers \
  categories/workflow/unified-dev-flow/scripts/test_unified_workflow_providers.py
git commit -m "feat: add unified workflow verification providers"
```

---

### Task 6: Thin CLI, End-to-End Flow, and Router Documentation

**Files:**
- Create: `categories/workflow/unified-dev-flow/scripts/unified_workflow/cli.py`
- Create: `categories/workflow/unified-dev-flow/scripts/unified-workflow`
- Create: `categories/workflow/unified-dev-flow/scripts/test_unified_workflow_cli.py`
- Create: `categories/workflow/unified-dev-flow/scripts/test_unified_workflow_e2e.py`
- Modify: `categories/workflow/unified-dev-flow/SKILL.md`
- Modify: `categories/workflow/unified-dev-flow/references/policy-model.md`

**Interfaces:**
- Produces `main(argv: Sequence[str] | None = None) -> int` and executable wrapper.
- CLI commands match design section 10 and accept JSON documents through named file arguments, never arbitrary verification strings.
- Exit codes are exactly `0 success`, `2 invalid arguments/contract`, `3 gate denied`, `4 corrupt state`, `5 lock busy`, `6 provider failure`, `7 request in doubt`.

- [ ] **Step 1: Write CLI and E2E tests first**

Run the wrapper through `subprocess.run` against a temporary Git project. Cover stable JSON output/exit codes and this complete flow:

```text
init working_tree route → add A and B(B depends A) → ready/start/report A
→ failed verification recorded → fix → successful verification
→ fresh MERGE_READY assertion → accept A → execute/accept B
→ modify A verification input → A and B become stale
→ re-ready/reverify/reaccept A and B
→ record working_tree delivery bound to current acceptance_set_sha256
→ complete run → replay produces byte-equivalent canonical state
```

Additional CLI cases: patch init exits 3; malformed schema exits 2; corrupt log exits 4; duplicate request returns identical JSON without duplicate side effect; in-doubt exits 7; unregistered command exits 6; status/replay do not write `.omc/`, `.superpowers/sdd/`, or `.codegraph/`.

- [ ] **Step 2: Run RED**

Run:

```bash
python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_cli.py
python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_e2e.py
```

Expected: fail because the wrapper and CLI module do not exist.

- [ ] **Step 3: Implement the thin CLI**

Use `argparse`. Each mutation requires `--request-id`; JSON contracts/assertions are loaded from explicit UTF-8 files. Map typed errors to the exact exit codes. `--json` prints one canonical JSON object; text mode is concise and contains the stable reason code on failure. The wrapper only imports `unified_workflow.cli.main` and exits with its return code.

- [ ] **Step 4: Document the runtime handoff**

In `SKILL.md`, add a concise Phase Two Runtime section stating that an eligible non-patch Route may be pinned into the Kernel, but the Router remains policy authority and Adapter execution is still external. In `policy-model.md`, define the finite obligations emitted into `RouteContract`; do not duplicate the runtime design or suggest the Kernel is required for legacy resume.

- [ ] **Step 5: Run focused GREEN**

Run:

```bash
python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_cli.py
python3 categories/workflow/unified-dev-flow/scripts/test_unified_workflow_e2e.py
```

Expected: all CLI and E2E tests pass with stable output.

- [ ] **Step 6: Run the full verification set**

```bash
for test_file in categories/workflow/unified-dev-flow/scripts/test_unified_workflow_*.py; do python3 "$test_file" || exit 1; done
python3 categories/workflow/unified-dev-flow/scripts/test_router_policy.py
python3 categories/workflow/unified-dev-flow/scripts/test_entry_gate_check.py
python3 categories/workflow/unified-dev-flow/scripts/test_session_brief.py
python3 categories/.system/skill-creator/scripts/quick_validate.py categories/workflow/unified-dev-flow
git diff --check
```

Expected: every command exits `0`; tests print no warnings or tracebacks.

- [ ] **Step 7: Commit**

```bash
git add categories/workflow/unified-dev-flow/scripts/unified_workflow/cli.py \
  categories/workflow/unified-dev-flow/scripts/unified-workflow \
  categories/workflow/unified-dev-flow/scripts/test_unified_workflow_cli.py \
  categories/workflow/unified-dev-flow/scripts/test_unified_workflow_e2e.py \
  categories/workflow/unified-dev-flow/SKILL.md \
  categories/workflow/unified-dev-flow/references/policy-model.md
git commit -m "feat: expose unified workflow runtime CLI"
```

---

## Final Review Contract

The whole-branch reviewer must verify:

1. Every spec section is implemented or explicitly remains a documented non-goal.
2. Reducer is the sole state authority and replay is deterministic.
3. Request reservation/resolution and `IN_DOUBT` cannot duplicate provider execution.
4. Stale evidence/acceptance/delivery cannot complete a Run.
5. Scope origin cannot be reset across fix retries.
6. Local verification makes no sandbox claim and does not execute arbitrary CLI strings.
7. No snapshot, generic workflow engine, legacy migration, Agent, Codex, Herdr, worktree, `.codegraph/` initialization, or unrelated repository change entered the branch.
8. Full verification commands have fresh passing evidence.
