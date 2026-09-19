#!/usr/bin/env python3
"""Black-box tests for entry-gate-check.py (the Entry Gate enforcer).

Contract under test:
  - Artifact: <project>/.omc/entry-gate-<sessionID>.md
  - BLOCK (exit 2) when missing / malformed; PASS (exit 0) when valid.
  - Runs with stdlib only:  python3 test_entry_gate_check.py

TDD: this file was written BEFORE entry-gate-check.py existed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry-gate-check.py")

VALID = """## 1. 理解和假设
用户要给 unified-dev-flow 加入口门禁；假设项目级文档由各项目自行维护。

## 2. 最小方案
- 只改一个文件，不动路由表。
- src/real.py

## 3. 范围纪律
只碰入口门禁直接相关的行；顺带发现只记录不动手。

## 4. 验证计划
先跑本测试脚本（RED），再实现脚本（GREEN）；验证命令：python3 scripts/test_entry_gate_check.py
"""

FAILURES = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def run(args: list[str], stdin_text: str = "",
        extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def write_artifact(proj: str, session: str, content: str) -> str:
    d = os.path.join(proj, ".omc")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"entry-gate-{session}.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return p


def main() -> None:
    check("script-exists", os.path.isfile(SCRIPT), "entry-gate-check.py missing (RED phase?)")
    if not os.path.isfile(SCRIPT):
        print(f"\n{len(FAILURES)} failure(s).")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as proj:
        os.makedirs(os.path.join(proj, "src"))
        open(os.path.join(proj, "src", "real.py"), "w").write("x = 1\n")
        # 1. missing artifact -> BLOCK
        r = run(["--project-dir", proj, "--session-id", "s-missing"])
        check("missing-artifact-blocks", r.returncode == 2, f"exit={r.returncode}")

        # 2. valid artifact -> PASS
        write_artifact(proj, "s-good", VALID)
        r = run(["--project-dir", proj, "--session-id", "s-good"])
        check("valid-artifact-passes", r.returncode == 0, f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 3. garbage content -> BLOCK
        write_artifact(proj, "s-garbage", "hello world, trust me bro\n")
        r = run(["--project-dir", proj, "--session-id", "s-garbage"])
        check("garbage-content-blocks", r.returncode == 2, f"exit={r.returncode}")

        # 4. headers but no file list in §2 -> BLOCK
        no_list = VALID.replace("- 只改一个文件，不动路由表。\n- src/real.py\n",
                                "只改一个文件，不动路由表。\n")
        write_artifact(proj, "s-nolist", no_list)
        r = run(["--project-dir", proj, "--session-id", "s-nolist"])
        check("missing-file-list-blocks", r.returncode == 2, f"exit={r.returncode}")

        # 5. headers + list but too short -> BLOCK
        tiny = "## 1. 理解和假设\n懂。\n\n## 2. 最小方案\n- 改 A\n\n## 3. 范围纪律\n不动别的。\n\n## 4. 验证计划\n跑测试。\n"
        write_artifact(proj, "s-tiny", tiny)
        r = run(["--project-dir", proj, "--session-id", "s-tiny"])
        check("too-short-blocks", r.returncode == 2, f"exit={r.returncode}")

        # 6. session isolation: A's artifact must not pass B
        r = run(["--project-dir", proj, "--session-id", "s-other"])
        check("session-isolation", r.returncode == 2, f"exit={r.returncode}")

        # 7. Claude-style stdin JSON contract
        payload = json.dumps({"session_id": "s-good", "cwd": proj, "tool_name": "Edit"})
        r = run([], stdin_text=payload)
        check("claude-stdin-contract", r.returncode == 0, f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 8. block reason goes to stderr (Claude reads stderr as the message)
        r = run(["--project-dir", proj, "--session-id", "s-missing"])
        check("reason-on-stderr", len(r.stderr.strip()) > 0, "empty stderr on block")

        # 9. SELF-EXEMPTION: writing the artifact itself must NOT deadlock.
        # No artifact exists yet; the write targeting it must pass.
        art = os.path.join(proj, ".omc", "entry-gate-s-self.md")
        r = run(["--project-dir", proj, "--session-id", "s-self", "--target", art])
        check("write-artifact-itself-passes", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 10. same via stdin tool_input.file_path (Claude/Trae shape)
        payload = json.dumps({"session_id": "s-self2", "cwd": proj,
                              "tool_input": {"file_path": art.replace("s-self", "s-self2")}})
        r = run([], stdin_text=payload)
        check("stdin-file-path-exemption", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 11. exemption is narrow: garbage artifact + code edit still BLOCKs
        write_artifact(proj, "s-narrow", "garbage, no headers at all\n")
        r = run(["--project-dir", proj, "--session-id", "s-narrow",
                 "--target", os.path.join(proj, "src", "code.py")])
        check("exemption-narrow-to-artifact", r.returncode == 2, f"exit={r.returncode}")

        # 12. apply_patch shape (Codex): Update File targeting artifact passes
        payload = json.dumps({
            "session_id": "s-patch", "cwd": proj, "tool_name": "apply_patch",
            "tool_input": {"command": "*** Begin Patch\n*** Update File: .omc/entry-gate-s-patch.md\n@@ -0,0 +1 @@\n+hi\n*** End Patch"}})
        r = run([], stdin_text=payload)
        check("apply-patch-artifact-passes", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

    # ---- Phase 2: scope validation + trail check ----
    phase2()
    phase2_trail()
    phase2_codegraph()
    phase_shim()
    phase3_logging()
    phase_blocklog_flag()
    phase4_review()

    print(f"\n{len(FAILURES)} failure(s)." if FAILURES else "\nAll tests passed.")
    sys.exit(1 if FAILURES else 0)


def make_artifact(proj: str, session: str, files: list[str]) -> None:
    body = ("## 1. 理解和假设\n做 Phase 2  scope 测试，假设路径提取按约定工作。\n\n"
            "## 2. 最小方案\n- 按约定列文件范围。\n"
            + "".join(f"- {f}\n" for f in files) +
            "\n## 3. 范围纪律\n只碰清单文件；顺带只记录。\n\n"
            "## 4. 验证计划\n先 RED 再 GREEN；命令：python3 scripts/test_entry_gate_check.py\n")
    write_artifact(proj, session, body)


def phase_shim() -> None:
    shim = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "entry-gate-antigravity.py")
    with tempfile.TemporaryDirectory() as proj:
        bindir = os.path.join(proj, "bin")
        os.makedirs(bindir)
        stub = os.path.join(bindir, "fake-checker.py")
        with open(stub, "w") as f:
            f.write("import sys\nsys.stderr.write('stub says no\\n')\n"
                    "sys.exit(int(sys.argv[1]))\n")
        env = {"PATH": os.environ.get("PATH", ""),
               "ENTRY_GATE_CHECKER_BIN": stub}
        payload = lambda: json.dumps(
            {"toolCall": {"name": "write_to_file", "args": {}},
             "conversationId": "c1", "workspacePaths": [proj]})

        # simpler: drive shim with a stub checker chosen by exit code
        def drive(code: int) -> dict:
            with open(stub, "w") as f:
                f.write(f"import sys\nsys.stderr.write('reason-{code}\\n')\n"
                        f"sys.exit({code})\n")
            r = subprocess.run(
                [sys.executable, shim], input=payload(),
                capture_output=True, text=True, timeout=30, env={**os.environ, **env})
            assert r.returncode == 0, f"shim must always exit 0, got {r.returncode}"
            return json.loads(r.stdout)

        # crash (exit 1) -> fail OPEN, never deny
        d = drive(1)
        check("shim-crash-failopen",
              d.get("decision") == "allow", f"got={d}")
        # validation block (exit 2) -> deny preserved
        d = drive(2)
        check("shim-block-still-denies",
              d.get("decision") == "deny" and "reason-2" in d.get("reason", ""),
              f"got={d}")

    # ---- shim --stop mode (Antigravity Stop contract) ----
    with tempfile.TemporaryDirectory() as proj:
        bindir = os.path.join(proj, "bin")
        os.makedirs(bindir)
        stub = os.path.join(bindir, "fake-checker.py")
        env = {"PATH": os.environ.get("PATH", ""),
               "ENTRY_GATE_CHECKER_BIN": stub}
        stop_payload = lambda: json.dumps(
            {"executionNum": 1, "terminationReason": "model_stop",
             "fullyIdle": True, "conversationId": "c-stop",
             "workspacePaths": [proj],
             "transcriptPath": os.path.join(proj, "t.jsonl")})

        def drive_stop(code: int) -> dict:
            with open(stub, "w") as f:
                f.write(f"import sys\nsys.stderr.write('reason-{code}\\n')\n"
                        f"sys.exit({code})\n")
            r = subprocess.run(
                [sys.executable, shim, "--stop"], input=stop_payload(),
                capture_output=True, text=True, timeout=30,
                env={**os.environ, **env})
            assert r.returncode == 0, f"shim --stop must exit 0, got {r.returncode}: {r.stderr[:200]}"
            return json.loads(r.stdout)

        d = drive_stop(2)
        check("shim-stop-block-continues",
              d.get("decision") == "continue" and "reason-2" in d.get("reason", ""),
              f"got={d}")
        d = drive_stop(0)
        check("shim-stop-pass-stops",
              d.get("decision") != "continue", f"got={d}")
        d = drive_stop(1)
        check("shim-stop-crash-failopen",
              d.get("decision") != "continue", f"got={d}")


def phase_blocklog_flag() -> None:
    # --block-log routes the row without touching os.environ
    with tempfile.TemporaryDirectory() as proj:
        logf = os.path.join(proj, "flag.jsonl")
        base_env = {k: v for k, v in os.environ.items() if k != "ENTRY_GATE_BLOCKLOG"}
        base_env["PATH"] = os.environ.get("PATH", "")
        r = subprocess.run(
            [sys.executable, SCRIPT, "--project-dir", proj, "--session-id", "s-f",
             "--block-log", logf],
            input="",
            capture_output=True, text=True, timeout=30, env=base_env)
        check("blocklog-flag-exit", r.returncode == 2, f"exit={r.returncode}")
        rows = []
        if os.path.isfile(logf):
            rows = [json.loads(line) for line in open(logf) if line.strip()]
        check("blocklog-flag-routes",
              len(rows) == 1 and rows[0].get("session") == "s-f", f"rows={rows}")
        check("blocklog-no-env-mutation",
              "ENTRY_GATE_BLOCKLOG" not in os.environ, "test env polluted")


def phase2() -> None:

    with tempfile.TemporaryDirectory() as proj:
        os.makedirs(os.path.join(proj, "src"))
        open(os.path.join(proj, "src", "real.py"), "w").write("x = 1\n")

        # 13. typo path (missing, no NEW:) -> BLOCK
        make_artifact(proj, "s-typo", ["src/real.py", "src/typoo.py"])
        r = run(["--project-dir", proj, "--session-id", "s-typo",
                 "--target", os.path.join(proj, "src", "real.py")])
        check("scope-typo-blocks", r.returncode == 2, f"exit={r.returncode}")

        # 14. NEW:-marked missing path passes
        make_artifact(proj, "s-new", ["src/real.py", "NEW: src/future.py"])
        r = run(["--project-dir", proj, "--session-id", "s-new",
                 "--target", os.path.join(proj, "src", "real.py")])
        check("scope-new-mark-passes", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 15. marker caching: valid -> pass + marker; unchanged rerun passes;
        #     artifact edited (typo added, mtime newer) -> re-validates -> blocks
        make_artifact(proj, "s-cache", ["src/real.py"])
        r = run(["--project-dir", proj, "--session-id", "s-cache",
                 "--target", os.path.join(proj, "src", "real.py")])
        check("scope-first-pass", r.returncode == 0, f"exit={r.returncode}")
        marker = os.path.join(proj, ".omc", ".scope-ok-s-cache")
        check("scope-marker-written", os.path.isfile(marker), "marker missing")
        r = run(["--project-dir", proj, "--session-id", "s-cache",
                 "--target", os.path.join(proj, "src", "real.py")])
        check("scope-rerun-passes", r.returncode == 0, f"exit={r.returncode}")
        import time as _t
        _t.sleep(0.05)
        make_artifact(proj, "s-cache", ["src/real.py", "src/broken-typo.py"])
        r = run(["--project-dir", proj, "--session-id", "s-cache",
                 "--target", os.path.join(proj, "src", "real.py")])
        check("scope-edit-revalidates", r.returncode == 2, f"exit={r.returncode}")


def phase2_trail() -> None:
    with tempfile.TemporaryDirectory() as proj:
        def transcript(n_edits: int) -> str:
            p = os.path.join(proj, "t.jsonl")
            with open(p, "w") as f:
                for _ in range(n_edits):
                    f.write('{"name": "Edit", "args": {}}\n')
            return p

        base = ["--check-trail", "--project-dir", proj]
        # 16. small work (< threshold) passes with no trail
        r = run(base + ["--transcript", transcript(2)])
        check("trail-small-passes", r.returncode == 0, f"exit={r.returncode}")

        # 17. complex work + missing trail -> BLOCK
        r = run(base + ["--transcript", transcript(10)])
        check("trail-missing-blocks", r.returncode == 2, f"exit={r.returncode}")

        # 18. complex work + fresh non-empty trail -> PASS
        with open(os.path.join(proj, "decisions.tsv"), "w") as f:
            f.write("date\tdecision\twhy\tevidence\tresult\n2026-09-07\tused X\tY\tfile.py\tok\n")
        r = run(base + ["--transcript", transcript(10)])
        check("trail-fresh-passes", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 19. stale trail (yesterday) -> BLOCK
        import time
        old = time.time() - 86400 * 2
        os.utime(os.path.join(proj, "decisions.tsv"), (old, old))
        r = run(base + ["--transcript", transcript(10)])
        check("trail-stale-blocks", r.returncode == 2, f"exit={r.returncode}")

    # ---- Stop-loop guard: give up loudly instead of spinning forever ----
    with tempfile.TemporaryDirectory() as proj:
        tp = os.path.join(proj, "t.jsonl")
        with open(tp, "w") as f:
            f.write('{"name": "Edit"}\n' * 10)
        base = ["--check-trail", "--project-dir", proj, "--transcript", tp,
                "--session-id", "s-loop", "--max-blocks", "3"]
        codes = [run(base).returncode for _ in range(4)]
        check("trail-giveup-sequence", codes == [2, 2, 2, 0], f"codes={codes}")

        # a pass resets the counter: fresh trail -> 0, then missing -> 2 again
        with open(os.path.join(proj, "decisions.tsv"), "w") as f:
            f.write("date\tdecision\n2026-09-07\tdid X\n")
        check("trail-pass-resets",
              run(base).returncode == 0, "pass after giveup failed")
        os.remove(os.path.join(proj, "decisions.tsv"))
        check("trail-counter-reset",
              run(base).returncode == 2, "counter was not reset by pass")

        # Stop-shape stdin WITHOUT --transcript must still count edits
        # (stdin used to be consumed twice -> empty transcript -> false pass)
        tp2 = os.path.join(proj, "t2.jsonl")
        with open(tp2, "w") as f:
            f.write('{"name": "Write"}\n' * 10)
        payload = json.dumps({"session_id": "s-stdin", "cwd": proj,
                              "transcript_path": tp2})
        r = run(["--check-trail", "--session-id", "s-stdin"], stdin_text=payload)
        check("trail-stdin-single-read", r.returncode == 2,
              f"exit={r.returncode} (stdin transcript ignored?)")

        # Antigravity transcript dialect counts too (write_to_file etc.)
        tp3 = os.path.join(proj, "t3.jsonl")
        with open(tp3, "w") as f:
            for _ in range(6):
                f.write('{"step_index":1,"type":"X","status":"DONE","name":"replace_file_content"}\n')
            for _ in range(4):
                f.write('{"step_index":2,"type":"X","status":"DONE","name":"write_to_file"}\n')
        r = run(["--check-trail", "--project-dir", proj, "--session-id", "s-agy",
                 "--transcript", tp3])
        check("trail-agy-dialect-counts", r.returncode == 2,
              f"exit={r.returncode} (agy write tools not counted?)")


def phase2_codegraph() -> None:
    with tempfile.TemporaryDirectory() as proj:
        os.makedirs(os.path.join(proj, "src"))
        open(os.path.join(proj, "src", "real.py"), "w").write("x = 1\n")
        os.makedirs(os.path.join(proj, ".codegraph"))  # index present
        bindir = os.path.join(proj, "bin")
        os.makedirs(bindir)
        stub = os.path.join(bindir, "codegraph")
        with open(stub, "w") as f:
            # stub: knows only "knownsym"; mode via STUB_MODE env
            f.write("#!/usr/bin/env python3\nimport json, os, sys\n"
                    "mode = os.environ.get('STUB_MODE', 'hit')\n"
                    "if mode == 'boom': sys.exit(1)\n"
                    "term = sys.argv[-1]\n"
                    "print(json.dumps([{'name': term}]) if term == 'knownsym' else [])\n")
        os.chmod(stub, 0o755)
        env = {"PATH": bindir + os.pathsep + os.environ.get("PATH", "")}
        tgt = os.path.join(proj, "src", "real.py")

        # 20. missing path, symbol in index -> PASS
        make_artifact(proj, "s-cghit", ["src/real.py", "src/knownsym.py"])
        r = run(["--project-dir", proj, "--session-id", "s-cghit", "--target", tgt],
                extra_env=env)
        check("codegraph-hit-passes", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 21. missing path, symbol NOT in index -> BLOCK
        make_artifact(proj, "s-cgmiss", ["src/real.py", "src/nosuchsym.py"])
        r = run(["--project-dir", proj, "--session-id", "s-cgmiss", "--target", tgt],
                extra_env=env)
        check("codegraph-miss-blocks", r.returncode == 2, f"exit={r.returncode}")

        # 22. CLI broken -> fail OPEN (warn, pass)
        make_artifact(proj, "s-cgboom", ["src/real.py", "src/nosuchsym.py"])
        env2 = dict(env)
        env2["STUB_MODE"] = "boom"
        r = run(["--project-dir", proj, "--session-id", "s-cgboom", "--target", tgt],
                extra_env=env2)
        check("codegraph-broken-failopen", r.returncode == 0, f"exit={r.returncode}")

        # 23. slow CLI x3 paths: no deadline => ~45s; deadline => ~6s + pass.
        # Proves the scope budget caps hook-blocking wall time.
        import time as _time
        with open(stub, "w") as f:
            f.write("#!/usr/bin/env python3\nimport time\ntime.sleep(30)\nprint('[]')\n")
        make_artifact(proj, "s-cgslow",
                      ["src/real.py", "src/slow-a.py", "src/slow-b.py", "src/slow-c.py"])
        t0 = _time.monotonic()
        r = run(["--project-dir", proj, "--session-id", "s-cgslow", "--target", tgt],
                extra_env=env)
        dt = _time.monotonic() - t0
        check("scope-budget-caps-walltime",
              r.returncode == 0 and dt < 12 and "WARN" in r.stderr,
              f"exit={r.returncode} dt={dt:.1f}s")


def phase3_logging() -> None:

    with tempfile.TemporaryDirectory() as proj:
        os.makedirs(os.path.join(proj, "src"))
        open(os.path.join(proj, "src", "real.py"), "w").write("x = 1\n")
        logf = os.path.join(proj, "blocks.jsonl")
        env = {"ENTRY_GATE_BLOCKLOG": logf}

        def logged() -> list[dict]:
            if not os.path.isfile(logf):
                return []
            return [json.loads(line) for line in open(logf) if line.strip()]

        # 23. missing artifact block is logged with kind
        r = run(["--project-dir", proj, "--session-id", "s-l1"], extra_env=env)
        check("block-missing-exit", r.returncode == 2, f"exit={r.returncode}")
        rows = logged()
        check("block-missing-logged",
              len(rows) == 1 and rows[0].get("kind") == "missing"
              and rows[0].get("session") == "s-l1", f"rows={rows}")

        # 24. passes append nothing
        make_artifact(proj, "s-l2", ["src/real.py"])
        r = run(["--project-dir", proj, "--session-id", "s-l2",
                 "--target", os.path.join(proj, "src", "real.py")], extra_env=env)
        check("pass-logs-nothing", r.returncode == 0 and len(logged()) == 1,
              f"exit={r.returncode} rows={len(logged())}")

        # 25. scope block logged with kind=scope
        make_artifact(proj, "s-l3", ["src/typo-missing.py"])
        r = run(["--project-dir", proj, "--session-id", "s-l3",
                 "--target", os.path.join(proj, "src", "real.py")], extra_env=env)
        kinds = [x.get("kind") for x in logged()]
        check("block-scope-logged", r.returncode == 2 and "scope" in kinds,
              f"exit={r.returncode} kinds={kinds}")

        # 26. trail block logged with kind=trail
        tp = os.path.join(proj, "t.jsonl")
        with open(tp, "w") as f:
            f.write('{"name": "Edit"}\n' * 10)
        r = run(["--check-trail", "--project-dir", proj, "--transcript", tp],
                extra_env=env)
        kinds = [x.get("kind") for x in logged()]
        check("block-trail-logged", r.returncode == 2 and "trail" in kinds,
              f"exit={r.returncode} kinds={kinds}")

    # 27. weekly report renders counts from a fixture log
    with tempfile.TemporaryDirectory() as proj:
        logf = os.path.join(proj, "blocks.jsonl")
        with open(logf, "w") as f:
            f.write('{"ts": "2026-09-01T10:00:00", "kind": "missing", "session": "a", "project": "/p/x", "reason": "r1"}\n'
                    '{"ts": "2026-09-02T10:00:00", "kind": "scope", "session": "b", "project": "/p/x", "reason": "r2"}\n'
                    '{"ts": "2026-09-03T10:00:00", "kind": "missing", "session": "c", "project": "/p/y", "reason": "r3"}\n')
        report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry-gate-report.py")
        check("report-exists", os.path.isfile(report), "entry-gate-report.py missing (RED?)")
        if os.path.isfile(report):
            r = subprocess.run(
                [sys.executable, report, "--log", logf, "--days", "30"],
                capture_output=True, text=True, timeout=30)
            out = r.stdout
            check("report-counts", r.returncode == 0 and "total: 3" in out
                  and "missing: 2" in out and "scope: 1" in out, f"exit={r.returncode} out={out[:300]}")


def phase4_review() -> None:
    """--check-review: any source edit owes verify + review artifacts."""
    valid_verify = ("## S5 验证证据\n"
                    "- ai-slop-cleaner: deletion-first 瘦身完成，无多余 wrapper 与冗余代码\n"
                    "- pytest tests/x_test.py → exit 0（3 passed）\n"
                    "- rg -n -F 'Y' path/to/file.md → exit 0，命中 2 行\n")
    valid_review = ("## S6 评审结论\n"
                    "verdict: MERGE_READY\n"
                    "reviewer: subagent-reviewer-1\n"
                    "round: 1\n"
                    "google-code-review 无阻断项；三透镜审查全绿通过。\n")

    def write_review_files(proj: str, session: str,
                           verify: str | None = None,
                           review: str | None = None) -> None:
        d = os.path.join(proj, ".omc")
        os.makedirs(d, exist_ok=True)
        if verify is not None:
            with open(os.path.join(d, f"verify-{session}.md"), "w",
                      encoding="utf-8") as f:
                f.write(verify)
        if review is not None:
            with open(os.path.join(d, f"review-{session}.md"), "w",
                      encoding="utf-8") as f:
                f.write(review)

    def tooluse_line(name: str, path: str) -> str:
        return json.dumps({"message": {"content": [{
            "type": "toolUse", "name": name,
            "input": {"file_path": path}}]}}) + "\n"

    with tempfile.TemporaryDirectory() as proj:
        os.makedirs(os.path.join(proj, "src"))
        open(os.path.join(proj, "src", "real.py"), "w").write("x = 1\n")
        logf = os.path.join(proj, "blocks.jsonl")
        env = {"ENTRY_GATE_BLOCKLOG": logf}
        src_tp = os.path.join(proj, "t-src.jsonl")
        with open(src_tp, "w") as f:
            f.write(tooluse_line("Edit", "src/real.py"))

        # 28. zero source edits -> pass, no artifacts needed
        empty_tp = os.path.join(proj, "t-empty.jsonl")
        open(empty_tp, "w").write("")
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-none", "--transcript", empty_tp],
                extra_env=env)
        check("review-zero-edits-pass", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 29. only .omc artifact writes -> pass (not S4 edits)
        omc_tp = os.path.join(proj, "t-omc.jsonl")
        with open(omc_tp, "w") as f:
            f.write(tooluse_line("Write", ".omc/entry-gate-r-omc.md"))
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-omc", "--transcript", omc_tp],
                extra_env=env)
        check("review-omc-writes-excluded", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 30. source edit + missing artifacts -> BLOCK (verify first)
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-missing", "--transcript", src_tp],
                extra_env=env)
        rows = [json.loads(x) for x in open(logf) if x.strip()]
        check("review-missing-blocks",
              r.returncode == 2 and rows and rows[-1].get("kind") == "verify",
              f"exit={r.returncode} rows={rows[-1:]}")

        # 31. verify ok + review missing -> BLOCK kind=review
        write_review_files(proj, "r-half", verify=valid_verify)
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-half", "--transcript", src_tp],
                extra_env=env)
        rows = [json.loads(x) for x in open(logf) if x.strip()]
        check("review-half-blocks",
              r.returncode == 2 and rows and rows[-1].get("kind") == "review",
              f"exit={r.returncode} rows={rows[-1:]}")

        # 32. both valid -> PASS
        write_review_files(proj, "r-good", verify=valid_verify,
                           review=valid_review)
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-good", "--transcript", src_tp],
                extra_env=env)
        check("review-valid-passes", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 33. review without verdict -> BLOCK
        write_review_files(proj, "r-noverdict", verify=valid_verify,
                           review=valid_review.replace("verdict: MERGE_READY\n",
                                                      "结论：挺好的\n"))
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-noverdict", "--transcript", src_tp],
                extra_env=env)
        check("review-no-verdict-blocks", r.returncode == 2,
              f"exit={r.returncode}")

        # 34. review without round -> BLOCK
        write_review_files(proj, "r-noround", verify=valid_verify,
                           review=valid_review.replace("round: 1\n", ""))
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-noround", "--transcript", src_tp],
                extra_env=env)
        check("review-no-round-blocks", r.returncode == 2,
              f"exit={r.returncode}")

        # 34a. verify without ai-slop-cleaner -> BLOCK
        no_clean_verify = ("## S5 验证证据\n"
                           "- pytest tests/x_test.py → exit 0（3 passed）\n"
                           "- rg -n -F 'Y' path/to/file.md → exit 0，命中 2 行\n")
        write_review_files(proj, "r-noclean", verify=no_clean_verify, review=valid_review)
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-noclean", "--transcript", src_tp],
                extra_env=env)
        check("review-missing-cleaner-blocks", r.returncode == 2,
              f"exit={r.returncode}")

        # 34b. review without google-code-review -> BLOCK
        no_google_review = ("## S6 评审结论\n"
                            "verdict: MERGE_READY\n"
                            "reviewer: claude (self, micro tier)\n"
                            "round: 1\n"
                            "手动确认代码逻辑正常，无阻断项，准备合并上线。\n")
        write_review_files(proj, "r-nogoogle", verify=valid_verify, review=no_google_review)
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-nogoogle", "--transcript", src_tp],
                extra_env=env)
        check("review-missing-google-review-blocks", r.returncode == 2,
              f"exit={r.returncode}")

        # 35. patch-declared route passes without artifacts
        patch_gate = ("## 1. 理解和假设\n只看不改；delivery_target：patch。\n\n"
                      "## 2. 最小方案\n- 不写文件。\n\n"
                      "## 3. 范围纪律\n只读。\n\n"
                      "## 4. 验证计划\n无。\n")
        write_artifact(proj, "r-patch", patch_gate)
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-patch", "--transcript", src_tp],
                extra_env=env)
        check("review-patch-exempt", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 36. unreadable transcript falls back to blocking (conservative)
        blob_tp = os.path.join(proj, "t-blob.jsonl")
        with open(blob_tp, "w") as f:
            f.write('{"name": "Edit"}\n')
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-blob", "--transcript", blob_tp],
                extra_env=env)
        check("review-opaque-transcript-blocks", r.returncode == 2,
              f"exit={r.returncode}")

        # 37. anti-spin: --max-blocks 1 blocks once, then gives up loudly
        spin_tp = os.path.join(proj, "t-spin.jsonl")
        with open(spin_tp, "w") as f:
            f.write(tooluse_line("Write", "src/real.py"))
        args = ["--check-review", "--project-dir", proj,
                "--session-id", "r-spin", "--transcript", spin_tp,
                "--max-blocks", "1"]
        r1 = run(args, extra_env=env)
        r2 = run(args, extra_env=env)
        rows = [json.loads(x) for x in open(logf) if x.strip()]
        check("review-antispin-giveup",
              r1.returncode == 2 and r2.returncode == 0
              and any(x.get("kind") == "review-giveup" for x in rows),
              f"exits={r1.returncode},{r2.returncode}")

        # 38. xiyu-code-review is accepted alongside google-code-review
        write_review_files(proj, "r-xiyu",
                           verify="## S5 验证证据\n- ai-slop-cleaner 瘦身完成\n- pytest -> exit 0\n" + ("x" * 60),
                           review="## S6 评审结论\nverdict: MERGE_READY\nreviewer: claude\nround: 1\n"
                                  "xiyu-code-review 三透镜审查全绿，无阻断问题。\n" + ("y" * 30))
        r = run(["--check-review", "--project-dir", proj,
                 "--session-id", "r-xiyu", "--transcript", src_tp],
                extra_env=env)
        check("review-xiyu-code-review-passes", r.returncode == 0,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 39. --guard-pr blocks when no review artifact exists
        empty_proj = tempfile.mkdtemp(prefix="gate-pr-empty-")
        r = run(["--guard-pr", "--project-dir", empty_proj, "--branch", "agent/gemini/task1"])
        check("guard-pr-no-review-blocks", r.returncode == 1 and "门禁阻断" in r.stderr,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 40. --guard-pr blocks when verdict is NEEDS_FIXES
        nf_proj = tempfile.mkdtemp(prefix="gate-pr-nf-")
        write_review_files(nf_proj, "nf-session",
                           verify="## S5 验证证据\n- ai-slop-cleaner: deletion-first 完成\n- exit 0\n" + ("v" * 50),
                           review="## S6 评审结论\nverdict: NEEDS_FIXES\nreviewer: human\nround: 1\n"
                                  "google-code-review: 发现边界未处理。\n" + ("r" * 40))
        r = run(["--guard-pr", "--project-dir", nf_proj, "--branch", "agent/gemini/task2"])
        check("guard-pr-needs-fixes-blocks", r.returncode == 1 and "NEEDS_FIXES" in r.stderr,
              f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 41. --guard-pr passes when review is valid with MERGE_READY
        mr_proj = tempfile.mkdtemp(prefix="gate-pr-mr-")
        write_review_files(mr_proj, "mr-session",
                           verify="## S5 验证证据\n- ai-slop-cleaner: deletion-first 完成\n- exit 0\n" + ("v" * 50),
                           review="## S6 评审结论\nverdict: MERGE_READY\nreviewer: claude\nround: 1\n"
                                  "xiyu-code-review 三透镜审查全绿通过。\n" + ("r" * 40))
        r = run(["--guard-pr", "--project-dir", mr_proj, "--branch", "agent/gemini/task3"])
        check("guard-pr-merge-ready-passes", r.returncode == 0 and "门禁放行" in r.stdout,
              f"exit={r.returncode} stdout={r.stdout[:200]}")

        # 42. --guard-pr bypass with escape hatch UNIFIED_DEV_FLOW_SKIP_REVIEW=1
        r = run(["--guard-pr", "--project-dir", empty_proj, "--branch", "agent/gemini/task4"],
                extra_env={"UNIFIED_DEV_FLOW_SKIP_REVIEW": "1"})
        check("guard-pr-escape-hatch-passes", r.returncode == 0 and "UNIFIED_DEV_FLOW_SKIP_REVIEW=1" in r.stderr,
              f"exit={r.returncode}")

        # 43. --guard-push blocks for task branch without review
        push_input = "refs/heads/agent/gemini/task1 aaaaa refs/heads/agent/gemini/task1 bbbbb\n"
        r = run(["--guard-push", "--project-dir", empty_proj], stdin_text=push_input)
        check("guard-push-task-branch-blocks", r.returncode == 1 and "门禁阻断" in r.stderr,
              f"exit={r.returncode}")

        # 44. --guard-push allows deleting remote branch
        del_input = "refs/heads/agent/gemini/task1 0000000000000000000000000000000000000000 refs/heads/agent/gemini/task1 0000000000000000000000000000000000000000\n"
        r = run(["--guard-push", "--project-dir", empty_proj], stdin_text=del_input)
        check("guard-push-delete-branch-passes", r.returncode == 0,
              f"exit={r.returncode}")

        # 45. --guard-push allows pushing to main
        main_input = "refs/heads/main 11111 refs/heads/main 22222\n"
        r = run(["--guard-push", "--project-dir", empty_proj], stdin_text=main_input)
        check("guard-push-main-branch-passes", r.returncode == 0,
              f"exit={r.returncode}")

        # ── New: Self-attestation / review-write denial tests ──────────────────

        # 46. Main agent writing .omc/review-*.md is DENIED by PreToolUse gate
        with tempfile.TemporaryDirectory() as rev_proj:
            # Create a valid entry gate
            write_artifact(rev_proj, "rw-session", VALID)
            # Try to write a review file as main agent (simulate via --target pointing at review artifact)
            r = run(["--project-dir", rev_proj, "--session-id", "rw-session",
                     "--target", f"{rev_proj}/.omc/review-rw-session.md"])
            check("review-write-denied-by-gate", r.returncode == 2 and "DENY" in r.stderr,
                  f"exit={r.returncode} stderr={r.stderr[:300]}")

        # 47. validate_review rejects 'self' reviewer
        with tempfile.TemporaryDirectory() as rv_proj:
            write_review_files(rv_proj, "rv-self",
                               verify="## S5 验证证据\n- ai-slop-cleaner: deletion-first 完成\n- exit 0\n" + ("v" * 50),
                               review="## S6 评审结论\nverdict: MERGE_READY\nreviewer: self\nround: 1\n"
                                      "google-code-review 通过。\n" + ("r" * 40))
            r = run(["--guard-pr", "--project-dir", rv_proj, "--branch", "feat/test"])
            check("guard-pr-self-reviewer-blocks", r.returncode == 1 and "self" in r.stderr.lower(),
                  f"exit={r.returncode} stderr={r.stderr[:300]}")

        # 48. --guard-commit: no artifact at all blocks
        with tempfile.TemporaryDirectory() as gc_proj:
            subprocess.run(["git", "init", gc_proj], capture_output=True)
            subprocess.run(["git", "-C", gc_proj, "checkout", "-b", "feat/gate-test"], capture_output=True)
            r = run(["--guard-commit", "--project-dir", gc_proj])
            check("guard-commit-missing-blocks", r.returncode == 1,
                  f"exit={r.returncode} stderr={r.stderr[:300]}")

        # 49. --guard-commit: valid session-based artifact passes even without branch-named file
        with tempfile.TemporaryDirectory() as gc_proj2:
            subprocess.run(["git", "init", gc_proj2], capture_output=True)
            write_artifact(gc_proj2, "default", VALID)
            r = run(["--guard-commit", "--project-dir", gc_proj2, "--session-id", "default"])
            check("guard-commit-session-artifact-passes", r.returncode == 0,
                  f"exit={r.returncode} stderr={r.stderr[:300]}")

        # 50. --record-review: self reviewer is blocked
        with tempfile.TemporaryDirectory() as rr_proj:
            r = run(["--record-review", "--project-dir", rr_proj, "--session-id", "rr-s1",
                     "--reviewer", "self", "--verdict", "MERGE_READY"])
            check("record-review-self-reviewer-blocks", r.returncode == 1 and "self" in r.stderr.lower(),
                  f"exit={r.returncode} stderr={r.stderr[:200]}")

        # 51. --record-review: valid external reviewer succeeds and stamps diff_hash
        with tempfile.TemporaryDirectory() as rr2_proj:
            subprocess.run(["git", "init", rr2_proj], capture_output=True)
            r = run(["--record-review", "--project-dir", rr2_proj, "--session-id", "rr-s2",
                     "--reviewer", "gemini-pro-subagent", "--verdict", "MERGE_READY",
                     "--notes", "三透镜审查通过：行为正确/结构健康/交付就绪"])
            review_file = os.path.join(rr2_proj, ".omc", "review-rr-s2.md")
            check("record-review-valid-passes",
                  r.returncode == 0 and os.path.isfile(review_file) and "diff_hash" in open(review_file).read(),
                  f"exit={r.returncode} stdout={r.stdout[:200]}")

        # 52. diff_hash provenance: guard-pr blocks when diff changed after review
        with tempfile.TemporaryDirectory() as ph_proj:
            # Set up a minimal git repo with commits so compute_diff_hash can produce a real hash
            subprocess.run(["git", "init", ph_proj], capture_output=True)
            subprocess.run(["git", "-C", ph_proj, "config", "user.email", "test@test.com"], capture_output=True)
            subprocess.run(["git", "-C", ph_proj, "config", "user.name", "Test"], capture_output=True)
            main_file = os.path.join(ph_proj, "main.py")
            with open(main_file, "w") as f:
                f.write("x = 1\n")
            subprocess.run(["git", "-C", ph_proj, "add", "."], capture_output=True)
            subprocess.run(["git", "-C", ph_proj, "commit", "-m", "init"], capture_output=True)
            subprocess.run(["git", "-C", ph_proj, "checkout", "-b", "origin/main"], capture_output=True)
            subprocess.run(["git", "-C", ph_proj, "checkout", "-b", "feat/something"], capture_output=True)
            # Make a change on feat branch so diff is non-empty and has a real hash
            with open(main_file, "w") as f:
                f.write("x = 2\n")
            subprocess.run(["git", "-C", ph_proj, "add", "."], capture_output=True)
            subprocess.run(["git", "-C", ph_proj, "commit", "-m", "change"], capture_output=True)
            # Write review with a FAKE (mismatched) diff_hash
            write_review_files(ph_proj, "ph-session",
                               verify="## S5 验证证据\n- ai-slop-cleaner: deletion-first 完成\n- exit 0\n" + ("v" * 50),
                               review="## S6 评审结论\nverdict: MERGE_READY\nreviewer: gemini-pro\nround: 1\n"
                                      "code-review 通过\n"
                                      "diff_hash: 0000000000000000000000000000000000000000000000000000000000000001\n"
                                      + ("r" * 40))
            r = run(["--guard-pr", "--project-dir", ph_proj, "--session-id", "ph-session",
                     "--branch", "feat/something"])
            check("guard-pr-stale-diff-hash-blocks", r.returncode == 1 and "diff_hash" in r.stderr,
                  f"exit={r.returncode} stderr={r.stderr[:300]}")

        # 52b. validate_review rejects 'claude (self)' due to word-boundary regex
        with tempfile.TemporaryDirectory() as rv2_proj:
            write_review_files(rv2_proj, "rv-self2",
                               verify="## S5 验证证据\n- ai-slop-cleaner: deletion-first 完成\n- exit 0\n" + ("v" * 50),
                               review="## S6 评审结论\nverdict: MERGE_READY\nreviewer: claude (self, no-baseline)\nround: 1\n"
                                      "google-code-review 通过。\n" + ("r" * 40))
            r = run(["--guard-pr", "--project-dir", rv2_proj, "--branch", "feat/test2"])
            check("guard-pr-self-regex-blocks", r.returncode == 1 and "self" in r.stderr.lower(),
                  f"exit={r.returncode} stderr={r.stderr[:300]}")


        # 53. Stop hook hint no longer contains "15 秒" / "micro" shortcut wording
        with tempfile.TemporaryDirectory() as sh_proj:
            os.makedirs(os.path.join(sh_proj, "src"))
            with open(os.path.join(sh_proj, "src", "x.py"), "w") as f:
                f.write("x = 1\n")
            write_artifact(sh_proj, "sh-session", VALID)
            src_tp2 = os.path.join(sh_proj, "t.jsonl")
            with open(src_tp2, "w") as f:
                f.write(json.dumps({"message": {"content": [
                    {"type": "toolUse", "name": "Edit", "input": {"file_path": "src/x.py"}}]}}) + "\n")
            r = run(["--check-review", "--project-dir", sh_proj, "--session-id", "sh-session",
                     "--transcript", src_tp2])
            check("stop-hook-no-15sec-shortcut",
                  "15 秒" not in r.stderr and "micro 只需" not in r.stderr,
                  f"stderr={r.stderr[:300]}")
            check("stop-hook-hints-independent-review",
                  "独立" in r.stderr or "independent" in r.stderr.lower() or "flow:review" in r.stderr
                  or "严禁主" in r.stderr,
                  f"stderr={r.stderr[:300]}")


if __name__ == "__main__":
    main()
