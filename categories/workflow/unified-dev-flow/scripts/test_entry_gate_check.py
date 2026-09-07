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

    print(f"\n{len(FAILURES)} failure(s)." if FAILURES else "\nAll tests passed.")
    sys.exit(1 if FAILURES else 0)


def make_artifact(proj: str, session: str, files: list[str]) -> None:
    body = ("## 1. 理解和假设\n做 Phase 2  scope 测试，假设路径提取按约定工作。\n\n"
            "## 2. 最小方案\n- 按约定列文件范围。\n"
            + "".join(f"- {f}\n" for f in files) +
            "\n## 3. 范围纪律\n只碰清单文件；顺带只记录。\n\n"
            "## 4. 验证计划\n先 RED 再 GREEN；命令：python3 scripts/test_entry_gate_check.py\n")
    write_artifact(proj, session, body)


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


if __name__ == "__main__":
    main()
