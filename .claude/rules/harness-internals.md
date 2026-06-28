---
paths:
  - ".claude/**"
  - ".opencode/**"
  - ".github/agents/**"
  - "tools/**"
  - "docs/**"
  - "openspec/**"
---

# agent-harness internals (maintainer notes)

These notes load only while editing the harness's own machinery (the `paths`
above). They are irrelevant when using agent-harness to develop a target repo, so
they stay out of normal sessions. Grow this file as the harness evolves.

## Registered-project context injection
- The `<project-context>` / `<registered-projects>` block injected at session
  start is produced by the **engineering plugin** (atman-marketplace), not this
  repo: `plugins/engineering/hooks/scripts/inject-project-context.mjs`
  (SessionStart hook).
- OpenCode mirrors this via three top-level plugins under `.opencode/plugins/`:
  `inject-project-context-plugin.ts`, `inject-target-rules-plugin.ts`, and
  `post-format-project-plugin.ts`.
- Shared config/path/rule helpers live under `.opencode/plugins/lib/` so the
  top-level plugins can stay aligned with the three Claude Code hook scripts.
- The event mapping is:
  1. `inject-project-context-plugin.ts` uses `chat.message` to inject
    `<project-context>` once per session.
  2. `inject-target-rules-plugin.ts` uses `tool.execute.before` to queue sibling
    target repo instructions/rules after `Read` / `Edit` / `Write`, then
    `experimental.chat.system.transform` injects them into the following
    model turn.
  3. `post-format-project-plugin.ts` uses `tool.execute.after` to run
    best-effort `postToolFormatCommands` for edited sibling target repos.
- Input: `.claude/project-context.json` (gitignored, per-machine). Scaffold/edit
  via the plugin's `/setup-project-context`.
- A companion **PreToolUse** hook (`inject-target-rules.mjs`, same plugin) lazily
  injects a target repo's guidance on Read/Edit/Write of a file under that sibling
  repo — reproducing native cwd memory/rule loading for repos outside the cwd tree
  (which SessionStart can't cover). It injects (1) the repo's root instruction file
  (`CLAUDE.md` preferred, else `AGENTS.md`) in full, once per session per repo, and
  (2) the `.claude/rules/*.md` whose `paths:` front matter matches the touched file.
  De-duplicated per file per session; silent for cwd-local files. This replaced the
  old `instructions` path attribute (the hook no longer emits it at SessionStart).
- OpenCode cannot attach additional context to the same file-tool call in the
  exact way Claude Code's `PreToolUse` can. The harness plugin therefore queues
  the matching instructions/rules after the first touched sibling-repo file and
  applies them on the next model turn. This is an intentional compatibility
  tradeoff, not a bug.
- `postToolFormatCommands` continue to come from the same
  `.claude/project-context.json` file. Per-project command lists override the
  top-level default in both Claude Code and OpenCode.

## `.ff15/` is a separate concern
- `.ff15/` (config, projects, operations) belongs to the **FF15 VS Code
  extension**, not to context injection. It is NOT the source of the
  registered-project list. Gitignored / per-machine.

## MCP launchers
- `.opencode/mcp/serena-mcp-launcher.mjs` (+ context7 launcher) start the MCP
  servers. Serena pins `--python 3.11` (Windows Python 3.12+ has an OpenSSL bug).
