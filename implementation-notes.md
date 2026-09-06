# Implementation Notes

## Task: unify global skills through symlinks

Branch: `chore/unify-global-skill-symlinks`

## Understanding and assumptions

- `~/universal-skills/categories/` is the canonical local source for shared skills.
- Global tool skill directories should not keep duplicate copies of these skills when symlinks are supported.
- ZCode/Agents-managed built-in or well-known skills under `~/.agents/skills/` must be preserved. The sync script should only add universal-skills symlinks there and skip existing non-symlink entries.
- Cursor `.mdc` rules and Claude plugin cache are generated integration artifacts; they are not treated as duplicate source-of-truth skill folders.

## Decisions

- Changed Claude global skill sync from `cp -r` to per-skill symlinks so future runs do not recreate duplicate skill copies.
- Extended ZCode sync to also normalize `~/.zcode/skills/` symlinks to point directly at `~/universal-skills/categories/...`, instead of relying on a second hop through `~/.codex/skills/...`.
- Kept `~/.agents/skills/` as incremental-only sync to avoid deleting or overwriting ZCode/Agents built-in and well-known skills.
- Did not touch unrelated modified skill content in `categories/deployment/xiyu-server-deploy/SKILL.md`.

## Verification plan

- Run `bash -n sync.sh`.
- Run `bash sync.sh --no-projects --no-codex --no-gemini --no-kimi` to exercise Claude global/plugin sync and ZCode sync without broader project/network work.
- Verify `~/.claude/skills` contains symlinks and no copied skill directories.
- Verify representative `~/.zcode/skills/*` entries point directly to `~/universal-skills/categories/...`.
- Verify no broken symlinks in `~/.claude/skills`, `~/.zcode/skills`, and `~/.agents/skills`.
- Verify built-in ZCode/Agents skills such as `gstack`, `lark-doc`, and `autoplan` still have `SKILL.md` files.

## Task: optimize xiyu-server-deploy skill

## Decisions

- Added the requested direct server connectivity probe to `categories/deployment/xiyu-server-deploy/SKILL.md` under target environment establishment, because it is a safe read-only access check and belongs before deployment actions.
- Used `StrictHostKeyChecking=accept-new` rather than the older imported skill's `StrictHostKeyChecking=no` pattern, because it keeps first-connect convenience without permanently disabling host key verification.
- Kept the imported `xiyu-deploy` file unchanged; it appears to be an older, project-specific operational note rather than the canonical deployment workflow.

## Task: migrate xiyu-deploy imported details

## Decisions

- Migrated concrete non-secret environment details from `categories/imported/xiyu-deploy/SKILL.md` into `categories/deployment/xiyu-server-deploy/references/release-runbook.md` under a `Known Winbid Test Server` section.
- Did not copy literal smoke-test credentials from the imported skill. The runbook now explicitly warns not to record smoke passwords, DB passwords, Redis passwords, private keys, or copied env contents.
- Preserved the legacy key path and legacy SSH option pattern only as fallback guidance, while keeping `StrictHostKeyChecking=accept-new` as the preferred direct-probe/default.
- Summarized the old hand-written scp/systemctl steps rather than copying them verbatim, because the canonical runbook already prefers GitHub Actions and `scripts/release/remote-deploy.sh`.

## Task: optimize unified-dev-flow skill

## Findings

- `categories/security-review/SKILL.md` was single-level, but every `sync.sh` loop uses `categories/*/*` — the skill was never installed anywhere (`~/.config/opencode/skills/security-review` missing). S6 referenced a dead link.
- SKILL.md mandated `google-code-review` while WORKFLOW-MAP.md §2 claimed canonical was engineering `code-review`; SKILL never mentioned `code-review` at all.
- Medium route diverged: SKILL said `speckit-chain`, MAP §4 said hand-split `writing-plans` route; MAP §4 also lacked refactor/research rows that SKILL has.
- `WORKFLOW-MAP.md at the repo root` pointer was unreachable after install (flat per-skill symlinks).
- S0 missed the AGENTS.md ledger breakpoint-resume rule; S3→S4 exemption covered micro only while the small route also skips S3; `ai-release-engineer` gate covered all AI-assisted code (≈ everything); Intractable route listed标讯-specific `blueprint-driven-development` as generic fallback.
- `categories/imported/ai-slop-cleaner/` was an empty leftover dir.

## Decisions

- Moved skill to `categories/security/security-review/` via `git mv` (history preserved as `R`); deleted the empty imported dir; fixed the stale `security-review/` line in AGENTS.md.
- S6 rule kept as validated (`ai-slop-cleaner` + `google-code-review` mandatory) and added `code-review` as spec-consistency supplement for spec-bearing routes only; MAP §2 updated to match instead of contradicting.
- MAP §4 rewritten to SKILL's taxonomy (added refactor/research rows, bug keeps S6-light, medium/large use `speckit-chain`, large makes `architect` plan review explicit).
- Created `categories/workflow/unified-dev-flow/references/alternatives.md` (stage alternatives + domain table + debug ladder, all refs machine-verified) and repointed SKILL.md's Overview at it; installed copies get it free via whole-dir symlink.
- S0 now checks `.superpowers/sdd/progress.md` first (resume, no re-classify); exemption widened to micro+small with S5 never exempt; `ai-release-engineer` narrowed to `autopilot`/`ralph` unattended output; Intractable keeps `figure-it-out` only (blueprint users invoke it by name, covered by When-NOT-to-use).
- P2: S6 force-semantics live only in Gates; dropped the duplicate access-pattern bullet (kept in S3 + debug note in references); standing principles named (4) with rest on-demand; parallel trio disambiguated; description gained one English trigger sentence with no flow enumeration (article's probe lesson preserved); `standard-workflow` non-intercept declared.
- Also fixed stale `gstack-*` names in MAP (§2 S2/S6/S7: `spec`, `qa`/`qa-only`, `ship`, `canary` — verified against frontmatter).
- Left untouched: `skillify` duplicate (`categories/gstack/skillify` vs `categories/imported/skillify`, both `name: skillify`) — pre-existing, needs its own DUPLICATE_SKILL_NAMES decision; sync run refreshed an alias symlink inside the gstack dir, flagged as follow-up.

## Verification plan

- `quick_validate.py` on both touched skills → valid.
- Regex-extracted all backtick skill refs from SKILL.md (69) and alternatives.md (64) → all resolve to exactly one `categories/*/*/SKILL.md`, no duplicates.
- `./sync.sh --no-projects` → all global targets OK, `security-review` symlink now present in `~/.config/opencode/skills/` and `~/.claude/skills/`, SKILLS-INDEX.md + GEMINI.md rebuilt (`### security` section, real description).
- Project checkouts still hold old file copies (`--no-projects`); next full `./sync.sh` propagates.

## Task: stop generating Cursor skill rules

## Decisions

- Disabled the `sync_cursor_projects` call in `sync.sh` so future sync runs no longer generate `.cursor/rules/*.mdc` skill files.
- Left the `sync_cursor_projects` function in place for now rather than deleting it, so the behavior can be restored or converted into an explicit opt-in flag later with minimal risk.
- Updated `AGENTS.md` and `CLAUDE.md` to say Cursor skill rule generation is no longer part of the normal sync behavior.
- Did not delete existing project `.cursor/rules/*.mdc` files automatically because those are outside this repository and may include non-skill Cursor rules; cleanup should be a separate confirmed action.

## Task: sync Trae CN Agent skills

## Decisions

- Added Trae CN Agent as a first-class sync target at `~/.trae-cn/skills/` after confirming that directory exists locally and contains Trae-managed marketplace skills.
- Used incremental symlink sync rather than deleting/recreating the directory, because Trae CN stores marketplace and built-in skills in the same area and those should not be overwritten.
- Added `--no-trae-cn` for parity with other optional sync targets.
- Existing Trae CN non-symlink skills with the same name as universal skills are skipped, so Trae-managed marketplace installs remain authoritative unless manually removed.

## Task: remove duplicate Agent-visible skill copies

## Findings

- ZCode/Agent-visible skills were duplicated because both `~/.agents/skills/` and legacy `~/.zcode/skills/` contained universal-skills symlinks.
- `~/.zcode/skills/` was entirely universal-skills symlinks, so it acted as a second copy of the same skill set for agents that scan both locations.
- Some non-symlink skills remain under `~/.agents/skills/` and `~/.trae-cn/skills/`; those are tool-managed built-in/marketplace skills and are intentionally not removed automatically.

## Decisions

- Kept `~/.agents/skills/` as the single ZCode/Agent universal-skills sync target.
- Changed sync to remove old universal-skills symlinks from `~/.zcode/skills/` instead of recreating them.
- Did not delete non-symlink skills in `~/.agents/skills/` or `~/.trae-cn/skills/`, because those may be installed or managed by the tools themselves.

## Task: hide near-duplicate skills from sync targets

## Findings

- `categories/workflow/google-code-review/SKILL.md` and `categories/coding/google-style-code-review/SKILL.md` both declare `name: google-code-review` and contain highly overlapping Google-style review guidance.
- Frontmatter-name duplicate scan also reports `skill-creator` and `skill-installer` under both workflow and `.system`; those `.system` copies are not currently synced by the `categories/*/*` loops, so they are not part of the visible duplicate issue.

## Decisions

- Added an explicit `DUPLICATE_SKILL_NAMES` list in `sync.sh` instead of trying fuzzy matching at sync time. This keeps the behavior deterministic and avoids accidentally hiding unrelated skills with similar words.
- Added `google-style-code-review` to that list, keeping `workflow/google-code-review` as the canonical visible skill because both files use that canonical frontmatter name.
- Kept the duplicate source directory in the repository for now rather than deleting it automatically; sync targets now skip it and clean old universal-skills symlinks pointing to it.
- Applied the filter to Claude global/project/plugin, Codex, ZCode, Trae CN, and Kimi symlink sync paths.

## Task: fix post-commit hook hardcoded origin

## Decisions

- Hook step 3 hardcoded `git push origin "$branch"`, but this repo's remote is named `gitee` (no `origin`), so every commit's push step failed with "fatal: 'origin' does not appear to be a git repository".
- Replaced with upstream-aware detection: `git rev-parse --abbrev-ref @{u}` → fall back to first remote in `git remote` → skip if none. Works regardless of remote name.
- Updated wording from "推送到 GitHub" to "推送到远端" since the actual remote is Gitee, not GitHub.
