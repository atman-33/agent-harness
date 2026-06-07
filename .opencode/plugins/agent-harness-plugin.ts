import type { Plugin } from "@opencode-ai/plugin";

/**
 * agent-harness OpenCode Plugin
 *
 * Injects active project context (from agent-harness.yaml) into the
 * system prompt of every OpenCode session, equivalent to the GitHub
 * Copilot SessionStart hook in .github/hooks/active-project-context.json.
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

  return {
    /**
     * Append the agent-harness context XML to the system prompt
     * whenever the system prompt is assembled for an LLM call.
     */
    "experimental.chat.system.transform": async (_input, output) => {
      if (systemMessage && systemMessage.length > 0) {
        output.system.push(systemMessage);
      }
    },
  };
};

export default agentHarnessPlugin;
export { agentHarnessPlugin as server };
