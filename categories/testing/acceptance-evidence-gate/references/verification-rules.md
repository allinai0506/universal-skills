# Verification rules and limits

## Author a valid contract

Use `assets/contract.template.json` and customize it **outside the target repository**, or commit it with your project's agreed acceptance criteria **before** running checks.

- `work_item`: issue/PR task identifier.
- `criteria[]`: ID, testable behavior, `source` (`user`, `issue`, `approved-spec`), provenance `source_ref`, and `check_ids`.
- `checks[]`: ID, `kind` (`acceptance`, `unit`, `integration`, `static`, `build`), executable `argv` (no shell operators), and 1–3600 second timeout.
- Every criterion must have at least one mapped acceptance check. Extra unit/build/static checks can be included but cannot substitute for behavior-level acceptance.
- A statement like "looks correct" is not a verifiable criterion. A check like `true`, `echo`, or a test with no meaningful assertions is not acceptance proof.

## Meaning of command statuses

- `run exit 0`: configured commands exited 0 and repository HEAD and cleanliness stayed stable; a receipt was generated. It does **not** mean all requirements are really exercised.
- `run exit 1`: at least one configured command failed/timed out, or HEAD/worktree drifted during tests; inspect logs and fix before claiming completion.
- `verify exit 0`: receipt is intact, matches the exact contract and currently clean HEAD, contains all expected successful command executions, and is within freshness bound (default 24 hours).
- `verify exit 1`: failed acceptance gate. **No verified completion**. A receipt that is malformed, structurally broken, or edited after the run is reported here too — not as invalid input — so the reason for the failure is never masked.
- `anchor exit 0`: the receipt was validated (its digest recomputed, its HEAD still current) and committed to the anchor file. **This is not a judgement of the receipt's honesty** — see the anchoring section: the protection comes from the anchor's location.
- `anchor exit 2`: invalid input or environment (unreadable receipt, missing or mismatched digest, receipt belonging to a different HEAD, empty `--anchor`, an anchor path inside the repository, an unwritable anchor location, or an anchor that already exists).
- `exit 2`: invalid input or environment (e.g. dirty worktree before run, missing Git, invalid contract, unreadable receipt path). **No verified completion**.

## Anchoring a receipt (optional, defeats forged receipts)

The receipt digest detects **accidental** edits. It does not stop a determined
forger, because the claiming Agent can rewrite the receipt and recompute the
digest. An **anchor** closes that gap: the anchor is a small file that commits
to one receipt's digest, and it must live somewhere the claiming Agent cannot
write.

```bash
# 1. run the checks and produce a receipt
python3 scripts/acceptance_gate.py run --repo <repo> --contract <c.json> --out <out>

# 2. register the receipt's digest in an anchor, in a protected location
python3 scripts/acceptance_gate.py anchor \
  --repo <repo> --receipt <out>/receipt.json --anchor <protected>/evidence.json

# 3. verify against the anchor
python3 scripts/acceptance_gate.py verify \
  --repo <repo> --contract <c.json> \
  --receipt <out>/receipt.json --anchor <protected>/evidence.json
```

The anchor binds three things: the work item, the repository HEAD, and the
receipt digest. The HEAD it records is the one the receipt was produced at
(`repo_head_after`), not the HEAD at anchoring time — `anchor` refuses to
stamp a receipt whose HEAD is no longer current. With `--anchor` in place,
forging a passing receipt is no longer enough — the forger must also produce
an anchor committing to it, and the anchor is write-once (`anchor` refuses to
overwrite an existing file).

### Where the anchor must live

The protection comes from **the anchor's location**, not from the command.
Measured against an Agent that controls the whole workspace:

| Attack | Result |
| --- | --- |
| Forge the receipt (flip `exit_code`, recompute `receipt_sha256`) | **blocked** — `anchor does not commit to this receipt` |
| Overwrite an existing anchor via `anchor` | **blocked** — anchors are write-once |
| Edit the anchor file directly (leaving its `receipt_sha256` alone) | **blocked** — the committed digest no longer matches the receipt |
| Edit the anchor file directly **and** update its `receipt_sha256` to the forged receipt's | **NOT blocked** — equivalent to writing a new anchor |
| **Write a brand-new anchor that commits to the forged receipt** | **NOT blocked** — the Agent can do this itself |

The last two rows are the important ones: `verify --anchor` checks that the
anchor commits to the receipt, and **the Agent can produce such an anchor by
itself**. The command therefore adds no protection on its own. It becomes
meaningful only when the anchor is written by a party the Agent does not
control:

- **Good** — a path only CI, a reviewer, or another principal can write; a
  read-only mount; a repository the claiming Agent has no push access to; a
  directory whose write bits are removed (`chmod a-w`) **and** whose anchor
  file is itself `chmod 0444`. Note that the owner can always `chmod` the
  permissions back, so this is *auditable*, not a hard block; and that
  removing the directory's write bit alone is **not** enough — the anchor
  file keeps its own `0644` mode and can still be rewritten in place.
- **Weak** — a path inside the Agent's own workspace. The Agent can rewrite
  the anchor just as it can rewrite the receipt; the anchor then only proves
  self-consistency, and `verify --anchor` gives a false sense of assurance.
- **Note** — the `PreToolUse` hook in this repository intercepts `Edit` and
  `Write`, but **not** shell redirection. A path rule alone does not stop a
  `Bash` write; use OS-level write protection or an external principal.
- The anchor must live **outside** the repository: `anchor` refuses a path
  inside it, because that would dirty the worktree and make every later
  `verify` fail.

**Operational rule:** treat `verify --anchor` as meaningful only when the
anchor's path is *not* writable by the Agent. If the Agent chose the path and
wrote the file, the result proves nothing about execution.

Anchoring is **optional**. Without `--anchor`, `verify` behaves exactly as
before. Use it when the claim is adversarial: a security fix, a money or
permission path, a release, or any completion claim an independent party
must be able to trust.

## Trust boundaries

- The receipt carries a `receipt_sha256` digest over its own body, and `verify` recomputes it. This binds the recorded exit codes, log digests and contract digest together, so **accidental or naive post-run edits** — flipping `exit_code` to `0` in a failing receipt — are detected and the gate reports `BLOCKED`.
- **This gate does not defend against deliberate forgery on its own.** A party that can rewrite the receipt can also recompute the digest, and can fabricate a whole receipt (including its log files and digests) for a check that never ran. The digest is tamper-**evident**, not tamper-proof: no cryptographic signatures and no key the Agent cannot access are provided. **In this repository the adversary is the very Agent being gated**, so treat an unanchored receipt as a self-consistency check, not as proof of execution.
- An **anchor** (see above) changes that: once the receipt digest is committed in a location the Agent cannot write, forging requires rewriting that anchor too. The anchor's strength is exactly the strength of its location — an anchor inside the Agent's own workspace proves nothing beyond self-consistency.
- The gate deliberately executes `checks[].argv` in the selected repo. It does **not** sandbox commands. Explicitly inspect the contract before running it; avoid untrusted PR-supplied commands.
- The gate proves only observed command exit status and log integrity, **not** complete test coverage, test independence, or absence of all defects.
- `kind: "acceptance"` checks that are **obviously** vacuous are rejected at contract-load time: no-op commands (`true`, `false`, `echo`, `yes`), inline snippets that can only succeed (`pass`, `exit 0`, `sys.exit(0)`, `raise SystemExit(0)`, `os._exit(0)`), and a shell wrapper around a **single** no-op (`sh -c true`). This is a **heuristic blacklist, not a proof of non-vacuity**: an equivalent always-succeeding command expressed some other way (a test that asserts nothing, a wrapper the blacklist does not know) is not detected mechanically, and a shell snippet that chains several commands (`sh -c "echo x; pytest"`) is deliberately never treated as vacuous. The Agent's semantic review remains the real guarantee.
- Some acceptance checks intentionally contact services, mutate files, write DB records or need secrets. Those commands require separate authorization and safe environment setup.
- Do not put output into the worktree. Logs may contain sensitive information; store privately and review before distributing.
- The repo must be clean, so tests that intentionally generate untracked artifacts must be configured to use external temporary directories, or this gate will block.
- A matching HEAD does not prove external dependencies have not changed. Note nondeterminism and external version/config dependencies in report.
- Changes only to ignored files are not detected by Git cleanliness. If ignored configuration/assets affect the test, pin and document them separately.
- A timed-out check is terminated together with its process group, so ordinary child processes (a test runner that spawns servers) do not survive the gate. A child that deliberately escapes the group on its own (`setsid`, daemonize) is outside this guarantee.

## Agent's semantic review questions

1. Is every accepted criterion linked to one or more acceptance checks?
2. Do the checks assert the criterion's **observable outcome**, not implementation details alone?
3. Are both false-positive paths and at least relevant boundary cases handled?
4. Does the execution context actually match the intended product environment?
5. Are passing tests from the current commit? Is the contract source actually approved?

Any "no"/"unknown" on essential behavior means report `UNVERIFIED` even if the CLI prints `GATE: PASS`.
