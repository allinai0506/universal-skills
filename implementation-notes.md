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
