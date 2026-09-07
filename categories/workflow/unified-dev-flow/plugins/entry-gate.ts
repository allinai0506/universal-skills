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

// Trail reminder state (warn-only: OpenCode has no blocking stop event,
// so the human — not the hook — is the enforcement layer here).
const TRAIL_MIN_EDITS = 8
const editCounts = new Map<string, number>()
const trailWarned = new Set<string>()

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
    "tool.execute.after": async (input: any) => {
      const tool = String(input?.tool ?? "").toLowerCase()
      if (!GATED_TOOLS.has(tool)) return
      const sid = String((input as any)?.sessionID ?? "default")
      editCounts.set(sid, (editCounts.get(sid) ?? 0) + 1)
    },
    event: async ({ event }: any) => {
      if (!event || typeof event.type !== "string") return
      const sid = String(
        event?.properties?.sessionID ?? event?.sessionID ?? event?.session?.id ?? "",
      )
      if (event.type === "session.deleted") {
        if (sid) {
          editCounts.delete(sid)
          trailWarned.delete(sid)
        }
        return
      }
      if (event.type !== "session.idle" || !sid) return
      const n = editCounts.get(sid) ?? 0
      if (n < TRAIL_MIN_EDITS || trailWarned.has(sid)) return
      trailWarned.add(sid)
      const msg = `[entry-gate] session did ${n} file writes with no confirmed decisions.tsv — ask the agent to write one (show-me-your-work)`
      try {
        await ctx?.client?.app?.log?.({ body: { service: "entry-gate", level: "warn", message: msg } })
      } catch {
        /* log best-effort */
      }
      try {
        await execFileAsync("osascript", ["-e", `display notification "${msg}" with title "entry-gate"`])
      } catch {
        /* macOS-only notifier; absence must not break anything */
      }
    },
  }
}
