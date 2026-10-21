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
- `verify exit 1`: failed acceptance gate. **No verified completion**.
- `exit 2`: invalid input or environment (e.g. dirty worktree before run, missing Git, invalid contract). **No verified completion**.

## Trust boundaries

- The receipt carries a `receipt_sha256` digest over its own body, and `verify` recomputes it. This binds the recorded exit codes, log digests and contract digest together, so editing `exit_code` in a failing receipt to `0` is detected and the gate reports `BLOCKED`. It is tamper-**evident**, not tamper-proof: a party that can rewrite the receipt can also recompute the digest. No cryptographic signatures or secure attestation are provided.
- The gate deliberately executes `checks[].argv` in the selected repo. It does **not** sandbox commands. Explicitly inspect the contract before running it; avoid untrusted PR-supplied commands.
- The gate proves only observed command exit status and log integrity, **not** complete test coverage, test independence, or absence of all defects.
- `kind: "acceptance"` checks that can never fail (`true`, `echo`, `python -c pass`, …) are rejected at contract-load time, because such a command cannot produce acceptance evidence. The rule applies to `acceptance` kind only; other kinds may legitimately be no-op smoke checks.
- Some acceptance checks intentionally contact services, mutate files, write DB records or need secrets. Those commands require separate authorization and safe environment setup.
- Do not put output into the worktree. Logs may contain sensitive information; store privately and review before distributing.
- The repo must be clean, so tests that intentionally generate untracked artifacts must be configured to use external temporary directories, or this gate will block.
- A matching HEAD does not prove external dependencies have not changed. Note nondeterminism and external version/config dependencies in report.
- Changes only to ignored files are not detected by Git cleanliness. If ignored configuration/assets affect the test, pin and document them separately.
- A timed-out check is terminated together with its whole process group, so orphaned child processes (a test runner that spawns servers) do not survive the gate.

## Agent's semantic review questions

1. Is every accepted criterion linked to one or more acceptance checks?
2. Do the checks assert the criterion's **observable outcome**, not implementation details alone?
3. Are both false-positive paths and at least relevant boundary cases handled?
4. Does the execution context actually match the intended product environment?
5. Are passing tests from the current commit? Is the contract source actually approved?

Any "no"/"unknown" on essential behavior means report `UNVERIFIED` even if the CLI prints `GATE: PASS`.
