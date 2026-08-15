---
name: ai-release-engineer
description: Use when AI-generated code is ready for validation, merge, release, or production deployment; before PR merge verification, test/UAT/production promotion, canary or full rollout, or post-release rollback decisions.
---

# AI Release Engineer

## Purpose

Turn AI-generated code changes into a controlled production release.

Core rule:

**Evidence → Gate → Release → Observe → Rollback**

Do not declare a change "done", "safe", or "ready for production" from code inspection alone.

## Operating Rules

1. **Inspect before testing**
   - Read repository instructions and existing CI/CD conventions.
   - Identify the changed scope and affected user journeys.
   - Reuse existing test commands and deployment mechanisms.
   - Do not invent infrastructure when the repository already provides it.

2. **Test according to risk**
   - Always run the project's required build/compile checks.
   - Always run the relevant unit/integration tests.
   - Run API/integration tests when backend behavior, contracts, persistence, or integrations changed.
   - Run browser E2E for changed user journeys and every defined critical user journey affected by the change.
   - Run SonarQube or the repository's configured quality gate when it is part of CI.
   - Add focused regression tests for every fixed defect when practical.

3. **Never hide failures**
   - Do not delete, weaken, skip, or rewrite a test merely to obtain PASS.
   - Do not ignore flaky failures. Record them and determine whether the release gate allows them.
   - A failed required gate means **STOP** until the cause is resolved or an explicit human-approved exception exists.

4. **Evidence must be reproducible**
   Record:
   - commit SHA
   - changed scope
   - commands executed
   - test results
   - E2E scenarios executed
   - quality-gate result
   - artifact identifier/digest
   - deployment environment
   - known exceptions
   - rollback method

5. **Build once, promote the same artifact**
   - Build the release artifact once.
   - Promote that exact artifact from test → UAT → production.
   - Do not rebuild separately for each environment.
   - Prefer immutable versioned artifacts with a verifiable digest.

6. **Production requires rollback readiness**
   Before production:
   - identify the exact artifact to deploy
   - verify the rollback artifact/version
   - verify database migration compatibility and rollback strategy
   - define the health signals that determine success/failure
   - use canary/gradual rollout when supported and appropriate

7. **Production is observable**
   After deployment, verify:
   - application health
   - error rate
   - latency
   - key business metrics
   - critical user journey health
   - logs/traces where available

   If defined release thresholds are breached, stop rollout and rollback according to the release plan.

## Required Workflow

### Phase 1 — Understand

Before changing or releasing anything:

- Read `AGENTS.md`, `CLAUDE.md`, `README.md`, and relevant repository rules if present.
- Identify the user story and acceptance criteria.
- Identify affected modules, APIs, data, permissions, workflows, and critical user journeys.
- Identify the project's canonical build/test/deploy commands.

If acceptance criteria or release requirements are materially missing, do not invent business behavior. State the missing evidence.

### Phase 2 — Verify

Run checks from narrowest to broadest:

```text
Compile / Build
    ↓
Unit Tests
    ↓
Integration / API Tests
    ↓
Static / Quality Gate
    ↓
Targeted E2E
    ↓
Critical User Journey Regression
```

Do not automatically run every expensive test for every trivial change. Match verification depth to change risk.

### Phase 3 — Gate

A release is **PASS** only when every required gate is PASS.

Minimum gate:

```text
Build                 PASS
Relevant Unit Tests   PASS
Relevant Integration  PASS
Relevant E2E          PASS
Quality Gate          PASS
Critical Journey      PASS
Rollback Ready        YES
```

If a gate is not applicable, record `N/A` with the reason. Never silently omit it.

### Phase 4 — Package

Create or identify one immutable artifact:

```text
Commit SHA
    ↓
Build
    ↓
Artifact + version + digest
```

Record the artifact identity in the release evidence.

### Phase 5 — Promote

Promote the same artifact:

```text
Test → UAT → Production
```

Do not rebuild between environments.

Environment configuration and secrets may differ, but the application artifact must remain identical.

### Phase 6 — Observe

After deployment, compare production signals against the release baseline.

At minimum:

```text
Health
Error Rate
Latency
Critical Business Flow
Logs / Traces
```

Use the repository's existing observability tooling.

### Phase 7 — Rollback

Rollback first when the release causes a material production regression.

Do not use production as a debugging environment.

After rollback:

1. preserve evidence
2. identify the failure
3. create a regression test
4. fix the code
5. rerun the required gates
6. create a new artifact
7. release again

## Critical User Journeys

Maintain a small, explicit set of business-critical end-to-end flows.

Example:

```text
Upload invoice
→ Recognize invoice
→ Associate voucher
→ Submit archive
→ Approve
→ Archive completed
```

A change affecting any step must run the corresponding journey.

Prefer a small number of high-value journeys over a huge test catalog.

## Release Evidence

Use this compact record:

```text
Release: <version>
Commit: <sha>
Artifact: <name:version>
Digest: <digest>

Changed Scope:
- ...

Verification:
- Build: PASS
- Unit: PASS
- Integration/API: PASS/N/A
- E2E: PASS/N/A
- Quality Gate: PASS/N/A
- Critical Journey: PASS/N/A

Known Exceptions:
- None / ...

Deployment:
- Test: PASS
- UAT: PASS
- Production: PENDING/PASS

Rollback:
- Artifact/version: ...
- Procedure: ...
- Database compatibility: ...
```

## Stop Conditions

STOP and do not release when:

- required build fails
- required tests fail
- critical E2E fails
- quality gate fails
- artifact identity cannot be verified
- production rollback is not understood
- incompatible database migration is detected
- required acceptance criteria are not evidenced

An explicit, documented human exception may override a non-critical gate. The exception must record:

- who approved it
- what was waived
- why
- risk
- expiry/next action

Never silently bypass a gate.

## Completion Rule

The agent may say:

**"Ready for production"**

only when the required evidence exists and all release gates pass.

Otherwise say:

**"Not ready for production"**

and list the failed or missing evidence.
