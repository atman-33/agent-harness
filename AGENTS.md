# agent-harness

- This repository is a harness for AI agents that work on sibling development repositories.
- Start by reading `config/agent-harness.yaml`.
- If `config/agent-harness.yaml` does not exist, create it from `config/agent-harness.template.yaml` and then continue.
- Read only the settings required to resolve the active project. Do not scan unrelated project entries.
- Use the `active_project` value to load `projects/<active_project>.yaml`.
- Use that project file to locate the OpenSpec root, target repositories, any follow-up instruction files, and the preferred validation commands.
- Prefer paths stored relative to the agent-harness root.

## Expected local files

- `config/agent-harness.template.yaml` is the committed template.
- `config/agent-harness.yaml` is the local working config and may be gitignored.
- `projects/_template.yaml` is the committed template for project profiles.
- `projects/<project-id>.yaml` stores project-specific work-unit paths and guidance.
- If `projects/<active_project>.yaml` does not exist yet, create it from `projects/_template.yaml` and fill in the target repository details.

## Project profile schema

- `openspec_root`: path, relative to the agent-harness root, whose `openspec/` directory stores the change artifacts for this work unit.
- `primary_repo`: repository id to use when one repository must be chosen by default.
- `repos`: list of repositories participating in the work unit.
- `repos[].root`: path, relative to the agent-harness root, to the repository root.
- `repos[].follow_files`: optional files to read when working in that repository.
- `repos[].default_checks`: optional validation commands for that repository.

## Minimal workflow

1. Read `config/agent-harness.yaml`.
2. Resolve `active_project`.
3. Read `projects/<active_project>.yaml`.
4. Resolve `openspec_root`, `primary_repo`, and the participating `repos`.
5. Use `openspec_root` as the working root for OpenSpec artifact creation, updates, sync, verification, and archive operations.
6. Move to the relevant repository under `repos[].root` for implementation and validation work, then follow that repository's local instructions.