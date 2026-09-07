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


if __name__ == "__main__":
    main()
