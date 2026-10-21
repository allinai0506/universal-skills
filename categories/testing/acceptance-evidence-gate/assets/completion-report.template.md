# Acceptance evidence for <WORK_ITEM>

- **Result:** VERIFIED / UNVERIFIED / BLOCKED
- **Repository and HEAD:** <repository> @ <40-digit commit SHA>
- **Contract:** <path and SHA-256>
- **Receipt:** <path; include only if it exists>
- **Gate:** `run=<status>`, `verify=<status>`, <UTC completion timestamp>

| Criterion (approved source) | Actual behavior asserted | Check(s) | Observed result | Coverage reviewed? |
| --- | --- | --- | --- | --- |
| AC-01 (<source_ref>) | <observable test assertion> | <check ID> | PASS / FAIL / NOT RUN | YES / NO |

**Residual uncertainty:** <manual verification, external dependencies, security/regression risks, or "none known" with scope>

**Required next action if not VERIFIED:** <single concrete next step>

Do not label this report VERIFIED solely because the automated gate returned exit 0: acceptance relevance and assertion quality need a separate review.
