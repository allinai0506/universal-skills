// Entry Gate enforcer — OpenCode plugin.
//
// Same contract as scripts/entry-gate-check.py (single source of truth):
// before the agent's first Edit/Write in a session, the entry-gate artifact
// <project>/.omc/entry-gate-<sessionID>.md must exist and be well-formed.
// This plugin shells out to the Python checker and throws on failure,
// which blocks the tool call and surfaces the reason to the agent.
//
// Install: see references/enforcement.md (one-time setup).
import { execFile } from "node:child_process"
import { promisify } from "node:util"
import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"

const execFileAsync = promisify(execFile)

const GATED_TOOLS = new Set(["edit", "write"])

// Resolved at install time; override with ENTRY_GATE_CHECKER env.
function checkerPath(): string {
  if (process.env.ENTRY_GATE_CHECKER) return process.env.ENTRY_GATE_CHECKER
  const home = os.homedir()
  const candidates = [
    path.join(home, ".claude", "scripts", "entry-gate-check.py"),
    path.join(home, ".config", "opencode", "scripts", "entry-gate-check.py"),
  ]
  return candidates.find((p) => fs.existsSync(p)) ?? candidates[0]
}

export const EntryGate = async (ctx: any) => {
  const projectDir: string =
    ctx?.directory ?? ctx?.worktree ?? process.cwd()
  return {
    "tool.execute.before": async (input: any, output: any) => {
      const tool = String(input?.tool ?? "").toLowerCase()
      if (!GATED_TOOLS.has(tool)) return
      const sessionID = String(input?.sessionID ?? "default")
      const args: string[] = [checkerPath(), "--project-dir", projectDir, "--session-id", sessionID]
      const target = output?.args?.filePath ?? output?.args?.path ?? output?.args?.file
      if (typeof target === "string" && target.length > 0) args.push("--target", target)
      try {
        await execFileAsync("python3", args, { timeout: 10000 })
      } catch (err: any) {
        // Only exit code 2 is a validation verdict ("deny").
        // Anything else (missing script, crash, timeout) fails OPEN —
        // a crashing gate must never brick the session.
        const code = (err as any)?.code
        const reason = String(err?.stderr ?? err?.message ?? "entry gate check failed").trim()
        if (code === 2) throw new Error(reason)
        console.warn(`[entry-gate] checker failed (code=${code}), fail-open: ${reason}`)
        return
      }
    },
  }
}
