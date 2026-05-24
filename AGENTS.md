# agent-harness

- This repository is a harness for AI agents that work on sibling development repositories.
- Start by reading `config/agent-harness.yaml`.
- If `config/agent-harness.yaml` does not exist, create it from `config/agent-harness.template.yaml` and then continue.
- Read only the settings required to resolve the active project. Do not scan unrelated project entries.
- Use the `active_project` value to load `projects/<active_project>.yaml`.
- Use that project file to locate the target repository, any follow-up instruction files, and the preferred validation commands.
- Prefer repository-relative paths stored in the project file.

## Expected local files

- `config/agent-harness.template.yaml` is the committed template.
- `config/agent-harness.yaml` is the local working config and may be gitignored.
- `projects/_template.yaml` is the committed template for project profiles.
- `projects/<project-id>.yaml` stores project-specific paths and guidance.
- If `projects/<active_project>.yaml` does not exist yet, create it from `projects/_template.yaml` and fill in the target repository details.

## Minimal workflow

1. Read `config/agent-harness.yaml`.
2. Resolve `active_project`.
3. Read `projects/<active_project>.yaml`.
4. Move to the target repository and follow its local instructions.