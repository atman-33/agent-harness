import type { Plugin } from "@opencode-ai/plugin";
// `readFileSync` is the only Node API used here; importing it directly keeps the
// plugin self-contained without pulling in a wider @types/node dependency.
// @ts-ignore - node:fs types are not installed in this workspace.
import { readFileSync, existsSync } from "node:fs";

/**
 * project-context OpenCode Plugin
 *
 * Mirrors the Claude Code `engineering` plugin's SessionStart hook
 * (`inject-project-context.mjs`): it reads `<workspace>/.claude/project-context.json`
 * and injects an equivalent `<project-context>` XML block into the first user
 * message of every OpenCode session as a visible, non-synthetic part.
 *
 * The block is shown in the TUI chat area and is also delivered to the LLM as
 * part of the human turn, so each session starts with the registered project
 * paths and the openspec docs folder in context.
 */
const projectContextPlugin: Plugin = async (ctx, _options) => {
  const workspaceRoot = ctx.directory;

  // Resolve `.claude/project-context.json` relative to the workspace root.
  // Uses string concatenation to avoid a dependency on @types/node's `path`.
  const configPath =
    workspaceRoot.replace(/\/+$/, "") + "/.claude/project-context.json";

  // Build the <project-context> block once at plugin initialization time.
  const projectContext = buildProjectContext(configPath, workspaceRoot);

  // Track sessions that have already received the context message so it is
  // only shown once per session. OpenCode fires `chat.message` for every user
  // message, so we need this guard to satisfy the "session start only"
  // requirement without adding a new core hook.
  const contextInjectedSessions = new Set<string>();

  return {
    /**
     * Prefix the very first user message of a session with the full
     * <project-context> XML. The part is non-synthetic so it is rendered in
     * the TUI chat area and delivered to the LLM as part of the human turn.
     */
    "chat.message": async (input, output) => {
      if (contextInjectedSessions.has(input.sessionID)) {
        return;
      }
      contextInjectedSessions.add(input.sessionID);

      if (projectContext && projectContext.length > 0) {
        output.parts.unshift({
          id: makeEarlyPartId(),
          sessionID: output.message.sessionID,
          messageID: output.message.id,
          type: "text",
          text: projectContext,
          synthetic: false,
        });
      }
    },
  };
};

/**
 * Read `.claude/project-context.json` and build the `<project-context>` XML
 * block. Returns `null` (injecting nothing) when the config is missing,
 * malformed, or has no useful content, so a session is never broken by a bad or
 * absent config — matching the failure-tolerant behaviour of the Claude Code
 * SessionStart hook.
 */
function buildProjectContext(
  configPath: string,
  workspaceRoot: string,
): string | null {
  let raw: string;
  try {
    raw = readFileSync(configPath, "utf8");
  } catch {
    // No config file for this project: inject nothing.
    return null;
  }

  let config: ProjectContextConfig;
  try {
    config = JSON.parse(raw);
  } catch (err) {
    console.error(
      "[project-context] Failed to parse .claude/project-context.json:",
      err instanceof Error ? err.message : String(err),
    );
    return null;
  }

  const resolvedOpenspec = resolveOpenspecPath(config, workspaceRoot);
  const hasOpenspec = resolvedOpenspec !== "";
  const hasProjects =
    Array.isArray(config.projects) &&
    config.projects.some(
      (p) => p && typeof p.path === "string" && p.path.trim() !== "",
    );

  // Nothing useful configured -> inject nothing.
  if (!hasOpenspec && !hasProjects) {
    return null;
  }

  return buildXml(config, resolvedOpenspec);
}

/**
 * Resolve the openspec docs folder to inject. Mirrors the Claude Code hook:
 *   1. `config.openspecPath` when set and the folder exists on disk.
 *   2. Otherwise `<workspaceRoot>/openspec` (the working directory's openspec).
 * Returns "" when neither exists, so the <openspec> line is simply omitted.
 */
function resolveOpenspecPath(
  config: ProjectContextConfig,
  workspaceRoot: string,
): string {
  const candidate =
    typeof config.openspecPath === "string" ? config.openspecPath.trim() : "";
  if (candidate && existsSync(candidate)) {
    return candidate;
  }
  const fallback =
    workspaceRoot.replace(/\\/g, "/").replace(/\/+$/, "") + "/openspec";
  return existsSync(fallback) ? fallback : "";
}

interface ProjectEntry {
  name?: string;
  path?: string;
  summary?: string;
}

interface ProjectContextConfig {
  openspecPath?: string;
  projects?: ProjectEntry[];
}

/** Escape a string for use in XML text or a double-quoted attribute. */
function xmlEscape(value: string): string {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Build the <project-context> XML block from the parsed config. */
function buildXml(config: ProjectContextConfig, openspecPath: string): string {
  const lines = ["<project-context>"];

  if (openspecPath) {
    lines.push(`  <openspec path="${xmlEscape(openspecPath)}" />`);
  }

  const projects = Array.isArray(config.projects) ? config.projects : [];
  const validProjects = projects.filter(
    (p) => p && typeof p.path === "string" && p.path.trim() !== "",
  );

  if (validProjects.length > 0) {
    lines.push("  <registered-projects>");
    for (const project of validProjects) {
      const path = (project.path as string).trim();
      const name =
        typeof project.name === "string" && project.name.trim()
          ? project.name.trim()
          : path;
      const summary =
        typeof project.summary === "string" && project.summary.trim()
          ? project.summary.trim()
          : "";
      const attrs = `name="${xmlEscape(name)}" path="${xmlEscape(path)}"`;
      if (summary) {
        lines.push(`    <project ${attrs}>`);
        lines.push(`      <summary>${xmlEscape(summary)}</summary>`);
        lines.push("    </project>");
      } else {
        lines.push(`    <project ${attrs} />`);
      }
    }
    lines.push("  </registered-projects>");
  }

  lines.push("</project-context>");
  return lines.join("\n");
}

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

export default projectContextPlugin;
export { projectContextPlugin as server };
