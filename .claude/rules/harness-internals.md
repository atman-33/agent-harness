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
  De-duplicated per file per (session, agent context); silent for cwd-local files.
  This replaced the old `instructions` path attribute (the hook no longer emits it
  at SessionStart).
- De-dup is keyed per **agent context**, not just per session (plugin v0.10.1+).
  The hook runs as a fresh process each call and de-dups via a shared filesystem
  sentinel under the OS temp dir. A Claude Code sub-agent shares the parent's
  `session_id` AND `transcript_path` but has its own context window; its hook
  payload carries an `agent_id` (absent for the main session). The sentinel key is
  `session_id | agent_id(or "main") | file`. Keying on `session_id` alone (the
  pre-v0.10.1 bug) let a sub-agent's injection write the sentinel first, so the
  main session — reading the same repo later — was skipped and never received the
  CLAUDE.md. The live hook runs from
  `~/.claude/plugins/cache/atman-marketplace/engineering/<version>/`, not the
  `C:\repos\atman-marketplace` source; deploy fixes via version bump + `claude
  plugin update`.
- OpenCode cannot attach additional context to the same file-tool call in the
  exact way Claude Code's `PreToolUse` can. The harness plugin therefore queues
  the matching instructions/rules after the first touched sibling-repo file and
  applies them on the next model turn. This is an intentional compatibility
  tradeoff, not a bug.
- The OpenCode mirror does **not** need (and cannot do) the `agent_id` keying
  above. It runs as a long-lived process and de-dups via an in-memory
  `Map<sessionID, SessionState>`, and OpenCode runs each sub-agent in a distinct
  **child session** (`Session.parentID`) with its own `sessionID` — so the Map
  already isolates the main session from each sub-agent. Its `tool.execute.before`
  hook also exposes no agent identifier, only `{tool, sessionID, callID}`. So the
  session-id-sharing bug is structural to the Claude Code hook and does not apply
  to OpenCode.
- `postToolFormatCommands` continue to come from the same
  `.claude/project-context.json` file. Per-project command lists override the
  top-level default in both Claude Code and OpenCode.

## Extended rules: the second injection path (`.claude/rules-ex`)
- There are TWO rule-injection paths, both PreToolUse (Read/Edit/Write):
  1. `inject-target-rules` — loads a **target repo's own** `CLAUDE.md` +
     `.claude/rules` when a file under that registered sibling repo is touched.
     Rules live WITH the repo they govern. Depends on `project-context.json`.
  2. `inject-extended-rules` (engineering plugin v0.11.0+) — loads
     **workspace-local** rules from `<cwd>/.claude/rules-ex/*.md` and applies them
     to files in ANY repo via **cwd-relative globs**. `rules-ex` = the *extended*
     form of `.claude/rules`. Lets cross-cutting dev rules stay centralised in the
     harness (cwd) without modifying sibling target repos. Does NOT read
     `project-context.json` — only cwd + the rules-ex folder.
- Matching (path #2): the touched file is converted to a cwd-relative path
  (`path.relative`, preserving `..`) and matched against each rule's `paths:` with
  a strict, **root-anchored** glob (NO implicit leading double-star prefix, unlike
  `inject-target-rules`'s `matchesGlob`). `paths:` is REQUIRED — a rule with no
  `paths:` is skipped (a cross-cutting rule must declare scope). Example front
  matter: `paths: ["../atman-marketplace/plugins/**/*.mjs"]`. Output is wrapped in
  `<extended-rules>`; de-dup sentinel prefix is `claude-extended-rules-`.
- Both paths are registered as separate commands under one PreToolUse matcher in
  the engineering plugin's `hooks.json`; Claude Code concatenates their
  `additionalContext`. The OpenCode mirror is
  `.opencode/plugins/inject-extended-rules-plugin.ts` with helpers
  (`toCwdRelativePath`, `loadExtendedRules`) in `lib/project-context-core.ts`;
  de-dup uses `SessionState.loadedExtendedRules` keyed by sessionID.
- Live engineering hook runs from the plugin cache; deploy via version bump +
  `claude plugin update` (same as inject-target-rules).

## `.ff15/` is a separate concern
- `.ff15/` (config, projects, operations) belongs to the **FF15 VS Code
  extension**, not to context injection. It is NOT the source of the
  registered-project list. Gitignored / per-machine.

## MCP launchers
- `.opencode/mcp/serena-mcp-launcher.mjs` (+ context7 launcher) start the MCP
  servers. Serena pins `--python 3.11` (Windows Python 3.12+ has an OpenSSL bug).
