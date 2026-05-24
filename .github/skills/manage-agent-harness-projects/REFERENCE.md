# Manage Agent Harness Projects Reference

## Managed schema

Project profiles in `projects/*.yaml` use this shape:

```yaml
id: app-stack
openspec_root: .
primary_repo: frontend
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
- `primary_repo` must match one `repos[].id`.
- Each repo object must include `id` and `root`.
- `follow_files` and `default_checks` must be string lists.

## Helper script

Script path:

```text
.github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py
```

Available commands:

- `set-active`: update `config/agent-harness.yaml` to point `active_project` at an existing profile.
- `create-profile`: create `projects/<project-id>.yaml` from explicit CLI values.
- `update-profile`: update `openspec_root`, `primary_repo`, `summary`, or repo entries for an existing profile.
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
python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py set-active --project-id multi-agent-ff15-vscode
```

Create a new multi-repo profile:

```bash
python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py create-profile \
  --project-id app-stack \
  --openspec-root . \
  --primary-repo frontend \
  --summary "Frontend and backend are developed together." \
  --repo-json '{"id":"frontend","root":"../app-frontend","follow_files":["../app-frontend/README.md"],"default_checks":["npm run build"]}' \
  --repo-json '{"id":"backend","root":"../app-backend","follow_files":["../app-backend/README.md"],"default_checks":["npm test"]}'
```

Update an existing profile:

```bash
python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py update-profile \
  --project-id app-stack \
  --primary-repo frontend \
  --repo-json '{"id":"frontend","root":"../app-frontend","follow_files":["../app-frontend/README.md"],"default_checks":["npm run build","npm test"]}'
```

Validate a profile without requiring the referenced paths to exist yet:

```bash
python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py validate-profile --profile-path projects/_template.yaml --allow-missing-paths
```