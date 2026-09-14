---
name: cow-sandbox
version: "2026.09.14-1"
synced-at: "2026-09-14T10:51:02"
description: Use when starting non-trivial coding tasks that require workspace isolation without the overhead, branch locks, or residue of git worktrees. Uses macOS APFS (cp -cR) / Linux reflink copy-on-write snapshots for instant, zero-cost sandbox isolation.
---

# Copy-on-Write (CoW) Sandbox

Use this skill to create instant, zero-disk-overhead, isolated development sandboxes using filesystem-level Copy-on-Write (macOS APFS `cp -cR` or Linux `--reflink=auto`).

## Why CoW Sandbox over Git Worktrees?

Traditional `git worktree` creates linked directories that share `.git` repository internals, resulting in:
1. **Branch Collisions**: You cannot checkout a branch that is already active in another worktree or the main working tree.
2. **Metadata Residue**: Worktrees leave phantom records in `.git/worktrees/` that require pruning when abandoned.
3. **Locking Issues**: Index locks and reference locks can collide between concurrent agents.

**CoW Sandbox Advantages:**
- **Instant (Milliseconds)**: APFS clones the entire directory tree with pointer remapping in ~10ms.
- **Zero Initial Disk Overhead**: Blocks are shared at the filesystem extent level until modified.
- **Complete Decoupling**: Standalone `.git` copy inside the sandbox allows `git reset --hard`, `git clean -fd`, checking out any branch, or testing destructive commands without touching the developer's working tree.
- **Disposable**: Purging is a simple directory deletion (`rm -rf`) with zero git residue.

## When to Use

- Starting any non-trivial feature, bugfix, or refactoring task requiring an isolated environment.
- When `main` or `master` is protected, and working directly in the current repo checkout could risk dirty edits.
- Running parallel sub-agents on independent tasks.
- Testing destructive changes, build artifact purges, or dependency upgrades.

## When NOT to Use

- Trivial single-line typo or documentation edits (work in place with dirty tree check).
- When the user explicitly requests a persistent multi-worktree setup.

## Workflow

### 1. Create Sandbox

Run the included helper or native `cp -cR`:

```bash
# Using helper:
python3 categories/workflow/cow-sandbox/scripts/cow_sandbox.py create --source . --task-id <task-id> --branch feat/<task-id>

# Or directly on macOS (APFS):
SANDBOX_DIR="$HOME/.sandboxes/<task-id>"
mkdir -p "$HOME/.sandboxes"
cp -cR . "$SANDBOX_DIR"
git -C "$SANDBOX_DIR" checkout -b feat/<task-id>
```

### 2. Work in Sandbox

Change working directory into the sandbox for all subsequent operations:
- All commands, edits, test runs, and commits take place within `$SANDBOX_DIR`.
- The developer's main working tree remains 100% clean and unaffected.

### 3. Harvest Changes

When work is verified and approved:
- **Option A (Push branch)**: Push the branch directly from the sandbox to the remote:
  ```bash
  git -C "$SANDBOX_DIR" push -u origin feat/<task-id>
  ```
- **Option B (Patch export)**: Export diff and apply to source:
  ```bash
  git -C "$SANDBOX_DIR" diff main > /tmp/task.patch
  git apply /tmp/task.patch
  ```

### 4. Purge Sandbox

Once changes are committed or pushed:

```bash
# Using helper:
python3 categories/workflow/cow-sandbox/scripts/cow_sandbox.py purge --task-id <task-id>

# Or directly:
rm -rf "$HOME/.sandboxes/<task-id>"
```
