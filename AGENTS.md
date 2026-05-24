# agent-harness

- Respond in Japanese.
- Write documents and repository artifacts in English unless the user explicitly asks for another language.
- Use Serena MCP before investigating or implementing code.
- This repository is a harness for AI agents that coordinate work across sibling development repositories.

## Working Rules

- Start with `config/agent-harness.yaml`. If it does not exist, create it from `config/agent-harness.template.yaml`.
- Read only the settings needed to resolve `active_project`. Do not scan unrelated project entries.
- Load `projects/<active_project>.yaml` and use it to resolve `openspec_root`, `primary_repo`, `repos[].root`, `repos[].follow_files`, and `repos[].default_checks`.
- Prefer paths stored relative to the agent-harness root.
- For code investigation, implementation, and validation, activate the Serena project for the resolved target repository, not `agent-harness`.
- Activate `agent-harness` itself only when editing harness files such as `config/`, `projects/`, `.github/`, or repository-local skills and instructions.
- Treat provider choice as repository-specific. Follow the target repository's own instructions instead of assuming GitHub Copilot CLI or any other provider.

## Minimal Workflow

1. Read `config/agent-harness.yaml`.
2. Resolve `active_project`.
3. Read `projects/<active_project>.yaml`.
4. Use `openspec_root` for OpenSpec work.
5. Switch to the relevant repository under `repos[].root` for code work and follow that repository's local instructions.