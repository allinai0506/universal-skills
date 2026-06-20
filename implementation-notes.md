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
