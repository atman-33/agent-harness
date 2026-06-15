import type { Plugin } from "@opencode-ai/plugin";

/**
 * agent-harness OpenCode Plugin
 *
 * Injects active project context (from agent-harness.yaml) into the
 * system prompt of every OpenCode session, equivalent to the GitHub
 * Copilot SessionStart hook in .github/hooks/active-project-context.json.
 *
 * Additionally, the first user message of every session is prefixed with a
 * small XML summary of the loaded context so the user can see what context
 * was injected. This is intentionally emitted as a non-synthetic text part so
 * it appears in the TUI chat area.
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

  // Track sessions that have already received the visible context message so
  // it is only shown once per session. OpenCode fires `chat.message` for every
  // user message, so we need this guard to satisfy the "session start only"
  // requirement without adding a new core hook.
  const contextInjectedSessions = new Set<string>();

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

    /**
     * Prefix the very first user message of a session with a compact XML
     * summary of the injected context. The part is non-synthetic so it is
     * rendered in the TUI chat area.
     */
    "chat.message": async (input, output) => {
      if (contextInjectedSessions.has(input.sessionID)) {
        return;
      }
      contextInjectedSessions.add(input.sessionID);

      const contextXml = buildChatContextXml(systemMessage);
      if (contextXml) {
        output.parts.unshift({
          id: makeEarlyPartId(),
          sessionID: output.message.sessionID,
          messageID: output.message.id,
          type: "text",
          text: contextXml,
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

/**
 * Build a compact XML document summarising the injected agent-harness context.
 *
 * The input is the full `<tooling-context>` XML that is sent to the LLM as a
 * system message. We extract the active projects, repositories, and OpenSpec
 * path so the user sees a concise, clearly-labelled XML block in the chat.
 */
function buildChatContextXml(systemMessage: string | null): string | null {
  if (!systemMessage || !systemMessage.includes("<tooling-context>")) {
    return null;
  }

  const openspecMatch = systemMessage.match(/<openspec path="([^"]+)" \/>/);
  const openspecPath = openspecMatch ? openspecMatch[1] : null;

  const projects: string[] = [];
  const projectRegex = /<project id="([^"]+)"[^>]*>([\s\S]*?)<\/project>/g;
  let projectMatch: RegExpExecArray | null;

  while ((projectMatch = projectRegex.exec(systemMessage))) {
    const projectId = projectMatch[1];
    const projectBlock = projectMatch[2];

    const summaryMatch = projectBlock.match(/<summary>([\s\S]*?)<\/summary>/);
    const summaryAttr = summaryMatch
      ? ` summary="${summaryMatch[1].trim()}"`
      : "";

    const repos: string[] = [];
    const repoRegex =
      /<repo id="[^"]+" qualified-id="([^"]+)" root-path="([^"]+)"[^>]*>/g;
    let repoMatch: RegExpExecArray | null;

    while ((repoMatch = repoRegex.exec(projectBlock))) {
      repos.push(
        `      <repo qualified-id="${repoMatch[1]}" root-path="${repoMatch[2]}" />`,
      );
    }

    if (repos.length === 0) {
      projects.push(`    <project id="${projectId}"${summaryAttr} />`);
    } else {
      projects.push(
        `    <project id="${projectId}"${summaryAttr}>\n${repos.join("\n")}\n    </project>`,
      );
    }
  }

  if (projects.length === 0 && !openspecPath) {
    return null;
  }

  const lines = ["<agent-harness-context>"];

  if (projects.length > 0) {
    lines.push("  <active-projects>");
    lines.push(...projects);
    lines.push("  </active-projects>");
  }

  if (openspecPath) {
    lines.push(`  <openspec path="${openspecPath}" />`);
  }

  lines.push("</agent-harness-context>");

  return lines.join("\n");
}

export default agentHarnessPlugin;
export { agentHarnessPlugin as server };
