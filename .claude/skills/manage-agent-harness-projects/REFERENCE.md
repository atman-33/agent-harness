# Manage Agent Harness Projects Reference

## Managed schema

Project profiles in `.agents/harness/projects/*.yaml` use this shape:

```yaml
id: app-stack
openspec_root: .
repos:
  - id: frontend
    root: ../app-frontend
    follow_files:
      - ../app-frontend/README.md
    default_checks:
      - npm run build
summary: |
  Frontend and backend are developed as one work unit.
```

Rules enforced by the helper script:

- `openspec_root`, `repos[].root`, and `repos[].follow_files` must be relative to the agent-harness root.
- Each repo object must include `id` and `root`.
- `follow_files` and `default_checks` must be string lists.

## Helper script

Script path:

```text
.github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py
```

Available commands:

- `set-active`: update `.agents/harness/config/agent-harness.yaml` to set `active_projects` and the active OpenSpec source.
- `create-profile`: create `.agents/harness/projects/<project-id>.yaml` from explicit CLI values.
- `update-profile`: update `openspec_root`, `summary`, or repo entries for an existing profile.
- `validate-profile`: validate one profile and report warnings such as a missing `openspec/` directory.

## Repo JSON format

`create-profile` and `update-profile` accept one or more `--repo-json` values.
Each value must be a full JSON object like this:

```json
{"id":"frontend","root":"../app-frontend","follow_files":["../app-frontend/README.md"],"default_checks":["npm run build","npm test"]}
```

`update-profile` replaces a repo entry with the same `id`, or appends it if the repo id does not exist yet.

## Examples

Switch the active project:

```bash
python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py set-active --project-id multi-agent-ff15-vscode --openspec-mode project --openspec-project-id multi-agent-ff15-vscode
```

Switch multiple active projects while using the harness-local OpenSpec directory:

```bash
python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py set-active --project-id multi-agent-ff15-vscode --project-id another-project --openspec-mode harness
```

Create a new multi-repo profile:

```bash
python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py create-profile \
  --project-id app-stack \
  --openspec-root . \
  --summary "Frontend and backend are developed together." \
  --repo-json '{"id":"frontend","root":"../app-frontend","follow_files":["../app-frontend/README.md"],"default_checks":["npm run build"]}' \
  --repo-json '{"id":"backend","root":"../app-backend","follow_files":["../app-backend/README.md"],"default_checks":["npm test"]}'
```

Update an existing profile:

```bash
python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py update-profile \
  --project-id app-stack \
  --repo-json '{"id":"frontend","root":"../app-frontend","follow_files":["../app-frontend/README.md"],"default_checks":["npm run build","npm test"]}'
```

Validate a profile without requiring the referenced paths to exist yet:

```bash
python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py validate-profile --profile-path .agents/harness/projects/_template.yaml --allow-missing-paths
```