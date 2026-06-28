# agent-harness

A general-purpose AI agent harness. Always started from this directory; actual development work targets sibling repositories via project profiles.

# Key Directories

- `.ff15/projects/` — project profiles (one YAML per target repo); excluded from git, create per-machine
- `.ff15/config/config.yaml` — sets `active_projects` and `openspec` for the current session
- `.ff15/operations/` — workspace-local FF15 operation files
- `openspec/` — OpenSpec changes, specs, and config for the harness itself
- `docs/` — setup and tool guides

# Workflow

- Start Claude Code from this directory (`claude`), then work on sibling repos via the active project profile.
- To switch the target project, edit `.ff15/config/config.yaml` (`active_projects`, `openspec.project_id`).
- To add a new target project, copy `.ff15/projects/_template.yaml` and fill in `id`, `openspec_root`, and `repos[].root`.
- Run `/mcp` after startup to confirm `serena` and `context7` are connected.

# Rules

- Respond to the user in Japanese.
- Write plan files (created during plan mode) in Japanese.
- Write all documents and repository artifacts in English unless the user explicitly requests otherwise.
- When you Read/Edit/Write a file in a target repository, its instruction file (`CLAUDE.md`, or `AGENTS.md`) is auto-injected in full once per session as a `<target-project-instructions>` block, along with any matching `.claude/rules`. Follow that injected guidance while working in that repo.
- Call `serena initial_instructions` before investigating or implementing code in any target repository.
- Commit messages use Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `style:`, `refactor:`).
- After editing `.opencode/plugins/**/*.ts` or `.opencode/**/*.mjs`, run `npm run check` and confirm it passes before finishing.

<important>
This repo contains no application code. Never create application source files here. All implementation work belongs in the target sibling repository.
The serena MCP launcher pins Python 3.11. If serena fails with an OpenSSL error, check the launcher (`.opencode/mcp/serena-mcp-launcher.mjs` for OpenCode, or the engineering plugin's `mcp/serena-mcp-launcher.mjs` for Claude Code) and ensure `--python 3.11` is set (not 3.12+).
</important>
