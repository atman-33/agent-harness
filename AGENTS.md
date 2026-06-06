# agent-harness

- Respond in Japanese.
- Write documents and repository artifacts in English unless the user explicitly asks for another language.
- Use Serena MCP before investigating or implementing code.
- This repository is a harness for AI agents that coordinate work across sibling development repositories.

## Active Project Context

Treat the injected active project context as authoritative.
Inspect `.agents/harness/runtime/active-project-context.json` only when you need the resolved snapshot.
Re-read `.agents/harness/config/agent-harness.yaml` or the specific profiles listed in `active_projects` only when the user asks or the injected context is insufficient, and then read only the minimum settings needed.

## Working Rules

- Prefer paths stored relative to the agent-harness root.
- Use the injected `<openspec path="..." />` value for OpenSpec work.
- For code investigation, implementation, and validation, activate the Serena project for the resolved target repository, not `agent-harness`.
- Activate `agent-harness` itself only when editing harness files such as `.agents/harness/`, `.github/`, or repository-local skills and instructions.
- Treat provider choice as repository-specific. Follow that target repository's local instructions instead of assuming GitHub Copilot CLI or any other provider.
- Do not run git commit, git push, git reset, git rebase, or other history-changing or remote-affecting git commands unless the user explicitly instructs you to do so.
