import type { Plugin } from "@opencode-ai/plugin";

/**
 * agent-harness OpenCode Plugin
 *
 * Injects active project context (from agent-harness.yaml) into the first
 * user message of every OpenCode session as a visible, non-synthetic part.
 * The full <tooling-context> XML is shown in the TUI chat area and is also
 * received by the LLM as part of the human turn.
 */
const agentHarnessPlugin: Plugin = async (ctx, _options) => {
  const workspaceRoot = ctx.directory;

  // Resolve the Python injection script relative to the workspace root.
  // Uses string concatenation to avoid a dependency on @types/node.
  const scriptPath =
    workspaceRoot.replace(/\/+$/, "") +
    "/.agents/harness/tools/inject-active-project-context.py";

  let systemMessage: string | null = null;
  let pythonCmd: string | null = null;

  // Find an available Python interpreter (python3, python, or py on Windows)
  const candidates = ["python3", "python", "py"];
  for (const cmd of candidates) {
    try {
      await ctx.$`${cmd} --version`.quiet();
      pythonCmd = cmd;
      break;
    } catch {
      continue;
    }
  }

  // Build the context once at plugin initialization time.
  if (pythonCmd) {
    try {
      const result =
        await ctx.$`${pythonCmd} ${scriptPath} --output-system-message`.quiet();
      systemMessage = result.text().trim();
    } catch (err) {
      console.error(
        "[agent-harness] Failed to inject active project context:",
        err instanceof Error ? err.message : String(err),
      );
      // Continue without context injection rather than breaking the session.
    }
  } else {
    console.error(
      "[agent-harness] No Python interpreter found (tried python3, python, py). Skipping context injection.",
    );
  }

  // Track sessions that have already received the context message so it is
  // only shown once per session. OpenCode fires `chat.message` for every user
  // message, so we need this guard to satisfy the "session start only"
  // requirement without adding a new core hook.
  const contextInjectedSessions = new Set<string>();

  return {
    /**
     * Prefix the very first user message of a session with the full
     * <tooling-context> XML. The part is non-synthetic so it is rendered in
     * the TUI chat area and delivered to the LLM as part of the human turn.
     */
    "chat.message": async (input, output) => {
      if (contextInjectedSessions.has(input.sessionID)) {
        return;
      }
      contextInjectedSessions.add(input.sessionID);

      if (systemMessage && systemMessage.length > 0) {
        output.parts.unshift({
          id: makeEarlyPartId(),
          sessionID: output.message.sessionID,
          messageID: output.message.id,
          type: "text",
          text: systemMessage,
          synthetic: false,
        });
      }
    },
  };
};

/**
 * Generate a part ID that satisfies OpenCode's part identifier rules and
 * sorts before normally-generated part IDs.
 *
 * OpenCode orders parts by `PartTable.id` ascending, so the context part must
 * have a smaller id than the user's own text part. Normal ascending IDs use
 * the current timestamp; using a zero timestamp ("000000000000") guarantees
 * the context part renders first.
 */
function makeEarlyPartId(): string {
  const chars =
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  const suffix = Array.from({ length: 14 }, () =>
    chars[Math.floor(Math.random() * chars.length)],
  ).join("");
  return `prt_000000000000${suffix}`;
}

export default agentHarnessPlugin;
export { agentHarnessPlugin as server };
