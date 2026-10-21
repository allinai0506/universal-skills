#!/usr/bin/env python3
"""Acceptance evidence gate: execute approved checks and validate a bound receipt.

Python 3.9+ standard library only. No shell=True. Runs arbitrary configured
commands intentionally: review the contract before invoking `run`.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
VALID_SOURCES = {"user", "issue", "approved-spec"}
VALID_KINDS = {"acceptance", "unit", "integration", "static", "build"}

RECEIPT_DIGEST_FIELD = "receipt_sha256"

# Acceptance evidence must actually exercise behaviour. These commands exit 0
# unconditionally, so accepting them as acceptance checks would manufacture
# evidence out of nothing. This is a heuristic blacklist, not a proof of
# non-vacuity: see the trust boundaries in references/verification-rules.md.
VACUOUS_COMMANDS = {"true", "false", ":", "echo", "yes", "/bin/true", "/bin/false"}
# Lowercase: snippets are lowercased before comparison.
VACUOUS_SNIPPETS = {"pass", "", "true", "false", "exit 0", "exit 0;",
                    "sys.exit(0)", "sys.exit(0);", "raisesystemexit(0)",
                    "raisesystemexit(0);", "os._exit(0)"}
UNCONDITIONAL_EXIT_RE = re.compile(
    r"sys\.exit\(0\)|raise\s+systemexit\(0\)|os\._exit\(0\)")
SHELL_PROGRAMS = {"sh", "bash", "zsh", "dash", "ksh"}


class GateError(Exception):
    pass


def sha256_bytes(content):
    return hashlib.sha256(content).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def receipt_digest(receipt):
    """Digest over the receipt body, excluding the digest field itself.

    This binds the recorded exit codes to the contract digest and the log
    digests, so a receipt edited after the run — flipping ``exit_code`` to 0
    in a failing receipt — no longer validates. It is tamper-*evident*, not
    tamper-proof: a party that can rewrite the receipt can also recompute the
    digest, and can fabricate a whole receipt for a check that never ran. See
    the trust boundary section in references/verification-rules.md.
    """
    body = {k: v for k, v in receipt.items() if k != RECEIPT_DIGEST_FIELD}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    return sha256_bytes(canonical)


def seal_receipt(receipt):
    receipt[RECEIPT_DIGEST_FIELD] = receipt_digest(receipt)
    return receipt


ANCHOR_SCHEMA = "acceptance-evidence-anchor/1"


def write_anchor(anchor_path, receipt, repo_head):
    """Write an anchor committing to this receipt's digest.

    The anchor is the trust anchor: it must live somewhere the claiming Agent
    cannot write (see references/verification-rules.md). Writing it here is
    only half the mechanism — the protection comes from the file location,
    which is why the receipt digest is what gets committed rather than the
    receipt body.

    An existing anchor is never overwritten: re-anchoring would let the
    Agent replace a commitment it no longer wants to honour. Use a fresh
    path for a fresh receipt.
    """
    if anchor_path.exists():
        raise GateError(f"anchor already exists: {anchor_path} (anchors are write-once)")
    payload = {
        "schema": ANCHOR_SCHEMA,
        "work_item": receipt.get("work_item"),
        "repo_head": repo_head,
        "receipt_sha256": receipt[RECEIPT_DIGEST_FIELD],
        "anchored_at": iso(utc_now()),
    }
    anchor_path.parent.mkdir(parents=True, exist_ok=True)
    anchor_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return payload


def check_anchor(anchor_path, receipt, repo_head):
    """Validate the anchor against this receipt. Returns a list of problems."""
    problems = []
    try:
        payload = json.loads(anchor_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"anchor unreadable: {exc}"]
    if not isinstance(payload, dict):
        return ["anchor must be a JSON object"]
    if payload.get("schema") != ANCHOR_SCHEMA:
        problems.append("anchor schema mismatch")
    if payload.get("work_item") != receipt.get("work_item"):
        problems.append("anchor work_item mismatch")
    if payload.get("repo_head") != repo_head:
        problems.append("anchor HEAD mismatch (repo moved since anchoring)")
    if payload.get("receipt_sha256") != receipt.get(RECEIPT_DIGEST_FIELD):
        problems.append("anchor does not commit to this receipt")
    return problems


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def iso(ts):
    return ts.isoformat(timespec="seconds")


def git(repo, *args):
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateError(f"git unavailable: {exc}") from exc
    if proc.returncode != 0:
        raise GateError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def repo_state(repo):
    return {
        "head": git(repo, "rev-parse", "HEAD"),
        "clean": git(repo, "status", "--porcelain", "--untracked-files=all") == "",
    }


def ensure_object(value, context):
    if not isinstance(value, dict):
        raise GateError(f"{context} must be JSON object")


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def is_vacuous(argv):
    """True when a command cannot fail, i.e. it can never be acceptance evidence.

    Detects ``true``/``false``/``echo``-style commands, inline snippets such
    as ``python -c "pass"``, unconditional-exit snippets (``sys.exit(0)``), and
    shell wrappers around a *single* no-op (``sh -c true``).

    A heuristic blacklist: it cannot prove a command is meaningful, only that
    it is trivially not. It must also not reject meaningful commands, so a
    shell snippet that chains several commands (``sh -c "echo x; pytest"``)
    is never treated as vacuous.
    """
    if not argv:
        return True
    program = os.path.basename(argv[0]).lower()
    if program in VACUOUS_COMMANDS:
        return True
    is_shell = program in SHELL_PROGRAMS
    for index, arg in enumerate(argv[:-1]):
        if arg not in ("-c", "--command"):
            continue
        snippet = argv[index + 1].strip()
        if is_vacuous_snippet(snippet):
            return True
        if is_shell and is_single_noop(snippet):
            return True
    return False


def is_vacuous_snippet(snippet):
    """True when an inline snippet can only succeed, whatever the interpreter."""
    lowered = snippet.strip().lower()
    if lowered in VACUOUS_SNIPPETS:
        return True
    if lowered.replace(" ", "") in VACUOUS_SNIPPETS:
        return True
    # An unconditional exit, possibly behind an import: `import sys; sys.exit(0)`.
    return bool(UNCONDITIONAL_EXIT_RE.search(lowered))


def is_single_noop(snippet):
    """True when a shell snippet is exactly one no-op command.

    ``sh -c "true"`` is vacuous; ``sh -c "echo x; pytest"`` is not, because it
    runs a real command. Chained snippets are therefore never vacuous.
    """
    parts = [p for p in re.split(r"[;&|]+", snippet.strip()) if p.strip()]
    if len(parts) != 1:
        return False
    head = parts[0].strip().split()[0] if parts[0].strip().split() else ""
    return os.path.basename(head) in VACUOUS_COMMANDS


def load_contract(path):
    try:
        raw = path.read_bytes()
        obj = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise GateError(f"contract unreadable / invalid JSON: {exc}") from exc
    ensure_object(obj, "contract")
    if obj.get("schema_version") != 1 or not nonempty(obj.get("work_item")):
        raise GateError("contract must contain schema_version=1 and work_item")
    checks = obj.get("checks")
    criteria = obj.get("criteria")
    if not isinstance(checks, list) or not checks:
        raise GateError("checks must be nonempty list")
    if not isinstance(criteria, list) or not criteria:
        raise GateError("criteria must be nonempty list")
    check_index = {}
    for check in checks:
        ensure_object(check, "check")
        cid = check.get("id")
        if not isinstance(cid, str) or not NAME_RE.fullmatch(cid) or cid in check_index:
            raise GateError(f"invalid/duplicate check id: {cid!r}")
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or any(not nonempty(a) for a in argv):
            raise GateError(f"{cid}: argv must be nonempty string array")
        if check.get("kind") not in VALID_KINDS:
            raise GateError(f"{cid}: kind must be one of {sorted(VALID_KINDS)}")
        timeout = check.get("timeout_seconds")
        if type(timeout) is not int or not (1 <= timeout <= 3600):
            raise GateError(f"{cid}: timeout_seconds must be integer in 1..3600")
        if check["kind"] == "acceptance" and is_vacuous(argv):
            raise GateError(
                f"{cid}: acceptance check must exercise real behaviour; "
                f"vacuous command {argv!r} cannot produce acceptance evidence"
            )
        check_index[cid] = check
    criterion_ids = set()
    for item in criteria:
        ensure_object(item, "criterion")
        aid = item.get("id")
        if not isinstance(aid, str) or not NAME_RE.fullmatch(aid) or aid in criterion_ids:
            raise GateError(f"invalid/duplicate criterion id: {aid!r}")
        criterion_ids.add(aid)
        if not nonempty(item.get("description")) or item.get("source") not in VALID_SOURCES:
            raise GateError(f"{aid}: requires description and source user/issue/approved-spec")
        if not nonempty(item.get("source_ref")):
            raise GateError(f"{aid}: source_ref is required (issue ID or approved document)")
        links = item.get("check_ids")
        if not isinstance(links, list) or not links or len(set(links)) != len(links):
            raise GateError(f"{aid}: check_ids must be nonempty unique list")
        for link in links:
            if link not in check_index:
                raise GateError(f"{aid}: unknown check id {link!r}")
        if not any(check_index[link]["kind"] == "acceptance" for link in links):
            raise GateError(f"{aid}: must map to at least one acceptance check")
    return obj, sha256_bytes(raw)


def assert_outside_repo(repo, out):
    if out == repo or repo in out.parents:
        raise GateError("output must be outside repository to prevent dirty worktree")


def run_check(check, repo, log, env):
    """Execute one check in its own process group.

    The child runs in a new session so that a timeout can terminate the whole
    group. Killing only the direct child would leave grandchildren running
    (a test runner that spawns servers, for example) after the gate has already
    declared the check failed.
    """
    kwargs = {"cwd": str(repo), "stdout": log, "stderr": subprocess.STDOUT,
              "env": env}
    if hasattr(os, "setsid"):
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen(check["argv"], **kwargs)
    except OSError as exc:
        log.write(("EXEC ERROR: " + str(exc) + "\n").encode("utf-8", "replace"))
        return None, False
    try:
        code = proc.wait(timeout=check["timeout_seconds"])
        return code, False
    except subprocess.TimeoutExpired:
        terminate_group(proc)
        return None, True


def terminate_group(proc):
    """Kill the check's whole process group, then the child as a fallback."""
    if hasattr(os, "killpg"):
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            pass
    else:
        proc.kill()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def do_run(args):
    repo = Path(args.repo).resolve()
    contract_path = Path(args.contract).resolve()
    out = Path(args.out).resolve()
    assert_outside_repo(repo, out)
    contract, digest = load_contract(contract_path)
    before = repo_state(repo)
    if not before["clean"]:
        raise GateError("repository is dirty before checks: commit/stash changes and retry")
    if out.exists() and any(out.iterdir()):
        raise GateError("output directory is not empty; select a fresh directory")
    (out / "logs").mkdir(parents=True, exist_ok=True)
    start = utc_now()
    receipt = {"schema_version": 1, "work_item": contract["work_item"],
               "contract_sha256": digest, "repo_head_before": before["head"],
               "started_at": iso(start), "checks": []}
    env = os.environ.copy()
    # Prevent Python acceptance runners from changing a clean worktree by writing __pycache__.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for check in contract["checks"]:
        log_path = out / "logs" / (check["id"] + ".log")
        with open(log_path, "wb") as log:
            code, timed_out = run_check(check, repo, log, env)
        receipt["checks"].append({"id": check["id"], "argv": check["argv"],
                                  "exit_code": code, "timed_out": timed_out,
                                  "log_file": "logs/" + check["id"] + ".log",
                                  "log_sha256": sha256_file(log_path)})
    after = repo_state(repo)
    receipt.update({"repo_head_after": after["head"], "repo_clean_after": after["clean"],
                    "finished_at": iso(utc_now())})
    seal_receipt(receipt)
    (out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False,
                                      indent=2) + "\n", encoding="utf-8")
    passed = all(c["exit_code"] == 0 and not c["timed_out"] for c in receipt["checks"])
    bound = before["head"] == after["head"] and after["clean"]
    print(f"{'PASS' if (passed and bound) else 'FAIL'}: run evidence at {out / 'receipt.json'}")
    return 0 if passed and bound else 1


def parse_utc(value):
    """Parse a receipt timestamp, returning None when it is unusable.

    A malformed timestamp is evidence of a broken or edited receipt, not an
    invalid invocation, so it is reported as a gate failure (exit 1) rather
    than as invalid input (exit 2).
    """
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def do_verify(args):
    repo = Path(args.repo).resolve()
    contract, digest = load_contract(Path(args.contract).resolve())
    path = Path(args.receipt).resolve()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError(f"invalid receipt: {exc}") from exc
    try:
        receipt = json.loads(raw)
    except ValueError as exc:
        # An unreadable receipt is broken or edited evidence, not an invalid
        # invocation: report it as a gate failure so the reason is not masked.
        print(f"FAIL: receipt is not valid JSON ({exc})", file=sys.stderr)
        print("GATE: BLOCKED - do not claim verified completion")
        return 1
    if not isinstance(receipt, dict):
        print("FAIL: receipt must be a JSON object", file=sys.stderr)
        print("GATE: BLOCKED - do not claim verified completion")
        return 1
    problems = []
    if receipt.get("schema_version") != 1 or receipt.get("work_item") != contract["work_item"]:
        problems.append("receipt identity mismatch")
    if receipt.get("contract_sha256") != digest:
        problems.append("contract changed since run")
    # The digest binds the recorded exit codes and log digests to the contract
    # digest. Without it, editing `exit_code` in a failing receipt would make
    # the gate report PASS.
    sealed = receipt.get(RECEIPT_DIGEST_FIELD)
    if not isinstance(sealed, str) or not sealed:
        problems.append("receipt digest missing (receipt was not produced by this gate)")
    elif sealed != receipt_digest(receipt):
        problems.append("receipt digest mismatch (receipt modified after run)")
    current = repo_state(repo)
    if not current["clean"]:
        problems.append("worktree dirty after testing")
    if not (receipt.get("repo_clean_after") is True and
            receipt.get("repo_head_before") == current["head"] and
            receipt.get("repo_head_after") == current["head"]):
        problems.append("HEAD/state mismatch since testing")
    start = parse_utc(receipt.get("started_at"))
    finish = parse_utc(receipt.get("finished_at"))
    if start is None or finish is None:
        problems.append("receipt timestamp missing or malformed")
    else:
        age = (utc_now() - finish).total_seconds()
        if finish < start or age < -60 or age > args.max_age_hours * 3600:
            problems.append("receipt time invalid/expired")
    results = receipt.get("checks")
    if not isinstance(results, list):
        problems.append("receipt.checks must be a list")
        results = []
    result_map = {}
    for entry in results:
        if not isinstance(entry, dict) or not nonempty(entry.get("id")):
            problems.append("malformed check result")
            continue
        if entry["id"] in result_map:
            problems.append("duplicate check result")
        result_map[entry["id"]] = entry
    expected_ids = {c["id"] for c in contract["checks"]}
    if set(result_map) != expected_ids:
        problems.append("missing / unexpected checks")
    passed_ids = set()
    for check in contract["checks"]:
        item = result_map.get(check["id"])
        if item is None:
            continue
        if item.get("argv") != check["argv"]:
            problems.append(f"{check['id']}: executed command mismatch")
            continue
        expected_log = "logs/" + check["id"] + ".log"
        if item.get("log_file") != expected_log:
            problems.append(f"{check['id']}: log path mismatch")
            continue
        log = path.parent / expected_log
        if not log.is_file() or sha256_file(log) != item.get("log_sha256"):
            problems.append(f"{check['id']}: missing/modified log")
            continue
        if type(item.get("exit_code")) is not int or item["exit_code"] != 0 or item.get("timed_out") is not False:
            problems.append(f"{check['id']}: failed or timed out")
            continue
        passed_ids.add(check["id"])
    for criterion in contract["criteria"]:
        failed = [cid for cid in criterion["check_ids"] if cid not in passed_ids]
        if failed:
            problems.append(f"{criterion['id']}: missing passing evidence for {failed}")
    if getattr(args, "anchor", None):
        problems.extend(check_anchor(Path(args.anchor), receipt, current["head"]))
    if problems:
        for problem in problems:
            print("FAIL: " + problem, file=sys.stderr)
        print("GATE: BLOCKED - do not claim verified completion")
        return 1
    print("GATE: PASS - checks passed for current clean HEAD; Agent must still review semantic coverage")
    print(f"HEAD: {current['head']}")
    print(f"Criteria: {len(contract['criteria'])}; checks: {len(expected_ids)}; receipt: {path}")
    return 0


def do_anchor(args):
    """Register the receipt's digest in an anchor file.

    The anchor must be written to a location the claiming Agent cannot write
    (for example a path only a CI job or an independent reviewer can reach).
    The protection comes from that location, not from this command.
    """
    repo = Path(args.repo).resolve()
    path = Path(args.receipt).resolve()
    anchor_path = Path(args.anchor).resolve()
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError(f"invalid receipt: {exc}") from exc
    ensure_object(receipt, "receipt")
    digest = receipt.get(RECEIPT_DIGEST_FIELD)
    if not isinstance(digest, str) or not digest:
        raise GateError("receipt has no digest; re-run `run` to produce one")
    head = repo_state(repo)["head"]
    payload = write_anchor(anchor_path, receipt, head)
    print(f"ANCHORED: {anchor_path}")
    print(f"HEAD: {head}")
    print(f"receipt_sha256: {payload['receipt_sha256']}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run check commands and collect signed-by-hash logs")
    run.add_argument("--repo", required=True)
    run.add_argument("--contract", required=True)
    run.add_argument("--out", required=True, help="new output directory OUTSIDE repository")
    verify = sub.add_parser("verify", help="validate receipt against current repo HEAD")
    verify.add_argument("--repo", required=True)
    verify.add_argument("--contract", required=True)
    verify.add_argument("--receipt", required=True)
    verify.add_argument("--max-age-hours", type=float, default=24)
    verify.add_argument("--anchor", help="anchor file committing to this receipt (optional)")
    anchor = sub.add_parser("anchor", help="register the receipt digest in an anchor file")
    anchor.add_argument("--repo", required=True)
    anchor.add_argument("--receipt", required=True)
    anchor.add_argument("--anchor", required=True, help="anchor file path the Agent cannot write")
    args = parser.parse_args()
    try:
        if args.command == "verify" and not (0 < args.max_age_hours <= 8760):
            raise GateError("--max-age-hours must be within (0, 8760]")
        if args.command == "run":
            return do_run(args)
        if args.command == "anchor":
            return do_anchor(args)
        return do_verify(args)
    except GateError as exc:
        print("GATE ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
