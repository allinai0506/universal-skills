#!/usr/bin/env python3
"""Copy-on-Write (CoW) Sandbox Manager for AI Coding Agents.

Leverages macOS APFS clonefile (cp -cR) or Linux reflink (cp --reflink=auto -a)
to create instant, zero-cost, fully isolated filesystem sandboxes for non-trivial
coding tasks, eliminating branch conflicts, phantom state, and lingering
metadata from git worktrees.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_SANDBOX_ROOT = Path.home() / ".sandboxes"
HERDR_CLONE_ROOT = Path.home() / ".herdr-controller" / "clones"


def get_sandbox_root() -> Path:
    override = os.environ.get("COW_SANDBOX_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    if HERDR_CLONE_ROOT.parent.exists():
        return HERDR_CLONE_ROOT
    return DEFAULT_SANDBOX_ROOT


def run_cmd(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def create_cow_clone(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    system = platform.system()

    if system == "Darwin":
        # macOS APFS Copy-on-Write clonefile
        res = run_cmd(["cp", "-cR", str(source), str(target)])
    else:
        # Linux with btrfs/xfs/zfs/bcachefs reflink support
        res = run_cmd(["cp", "--reflink=auto", "-a", str(source), str(target)])
        if res.returncode != 0:
            # Fallback to standard copy if reflink completely fails
            res = run_cmd(["cp", "-a", str(source), str(target)])

    if not (target / ".git").exists():
        raise RuntimeError(
            f"Failed to create CoW clone from {source} to {target}: {res.stderr.strip() or res.stdout.strip()}"
        )


def sanitize_sandbox(sandbox: Path) -> None:
    """Reset uncommitted working tree edits and untracked files in the clone sandbox."""
    run_cmd(["git", "reset", "--hard", "HEAD"], cwd=sandbox)
    run_cmd(["git", "clean", "-fd"], cwd=sandbox)


def cmd_create(args: argparse.Namespace) -> None:
    source = Path(args.source or os.getcwd()).expanduser().resolve()
    if not (source / ".git").exists():
        sys.stderr.write(f"Error: {source} is not a valid git repository.\n")
        sys.exit(1)

    task_id = args.task_id
    if not task_id:
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        task_id = f"task-{ts}"

    root = get_sandbox_root()
    target = root / task_id

    if target.exists():
        if args.force:
            shutil.rmtree(target, ignore_errors=True)
        else:
            sys.stderr.write(f"Error: Sandbox already exists at {target}. Use --force to overwrite.\n")
            sys.exit(1)

    try:
        create_cow_clone(source, target)
        if args.sanitize:
            sanitize_sandbox(target)
        if args.branch:
            run_cmd(["git", "checkout", "-b", args.branch], cwd=target)
    except Exception as e:
        sys.stderr.write(f"Error creating CoW sandbox: {e}\n")
        sys.exit(1)

    result = {
        "status": "created",
        "task_id": task_id,
        "source": str(source),
        "sandbox_path": str(target),
        "created_at": datetime.datetime.now().isoformat(),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"✓ CoW Sandbox ready: {target}")
        print(f"  Source: {source}")
        print(f"  Task ID: {task_id}")


def cmd_purge(args: argparse.Namespace) -> None:
    root = get_sandbox_root()
    target = Path(args.sandbox).expanduser().resolve() if args.sandbox else (root / args.task_id)

    if not target.exists():
        sys.stderr.write(f"Error: Sandbox {target} does not exist.\n")
        sys.exit(1)

    # Safety check: ensure target is within sandbox root
    try:
        common = os.path.commonpath([root, target])
    except ValueError:
        common = None

    if common != str(root) or target == root:
        sys.stderr.write(f"Refusing to delete unsafe path outside sandbox root: {target}\n")
        sys.exit(1)

    shutil.rmtree(target, ignore_errors=True)
    if args.json:
        print(json.dumps({"status": "purged", "path": str(target)}))
    else:
        print(f"✓ CoW Sandbox purged: {target}")


def cmd_list(args: argparse.Namespace) -> None:
    root = get_sandbox_root()
    sandboxes = []
    if root.exists():
        for item in root.iterdir():
            if item.is_dir() and (item / ".git").exists():
                sandboxes.append(str(item))

    if args.json:
        print(json.dumps({"sandboxes": sandboxes}, indent=2))
    else:
        if not sandboxes:
            print(f"No active CoW sandboxes in {root}")
        else:
            print(f"Active CoW sandboxes in {root}:")
            for sb in sandboxes:
                print(f"  - {sb}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CoW Sandbox Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create a new CoW sandbox clone")
    p_create.add_argument("--source", "-s", default=".", help="Source repo path (default: current dir)")
    p_create.add_argument("--task-id", "-t", help="Task ID / sandbox folder name")
    p_create.add_argument("--branch", "-b", help="Branch to checkout in sandbox")
    p_create.add_argument("--sanitize", action="store_true", default=True, help="Clean untracked/dirty edits in clone")
    p_create.add_argument("--force", "-f", action="store_true", help="Overwrite existing sandbox")
    p_create.add_argument("--json", action="store_true", help="Output JSON result")

    # purge
    p_purge = sub.add_parser("purge", help="Purge an existing CoW sandbox")
    p_purge.add_argument("--task-id", "-t", help="Task ID")
    p_purge.add_argument("--sandbox", help="Direct path to sandbox")
    p_purge.add_argument("--json", action="store_true", help="Output JSON result")

    # list
    p_list = sub.add_parser("list", help="List active CoW sandboxes")
    p_list.add_argument("--json", action="store_true", help="Output JSON result")

    args = parser.parse_args()
    if args.command == "create":
        cmd_create(args)
    elif args.command == "purge":
        cmd_purge(args)
    elif args.command == "list":
        cmd_list(args)


if __name__ == "__main__":
    main()
