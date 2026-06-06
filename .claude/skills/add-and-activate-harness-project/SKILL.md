---
name: add-and-activate-harness-project
description: Creates an agent-harness project profile and updates the active session config to use it. Use when working in `agent-harness` and the user wants to add a repository under `.agents/harness/projects/`, create or update `.agents/harness/config/agent-harness.yaml`, or switch `active_projects` to a specific project.
---

# Add And Activate Harness Project

## Quick start

Create the profile:

```bash
python3 .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py create-profile \
  --project-id my-project \
  --openspec-root ../my-project \
  --summary "Short project summary." \
  --repo-json '{"id":"my-project","root":"../my-project","default_checks":["npm run compile"]}'
```

Activate it:

```bash
python3 .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py set-active \
  --project-id my-project \
  --openspec-mode project \
  --openspec-project-id my-project
```

## Workflows

1. Confirm the target repository root and choose a stable `project_id`.
2. Treat all paths as relative to the `agent-harness` repository root.
3. If the profile does not exist, create `.agents/harness/projects/<project-id>.yaml` with the helper script.
4. Add one or more `--repo-json` entries with repo `id`, `root`, and optional `follow_files` or `default_checks`.
5. Run `validate-profile` immediately after creating or updating the profile.
6. Run `set-active` to write `.agents/harness/config/agent-harness.yaml` with the intended `active_projects` and OpenSpec source.
7. Verify the resolved session context with `.agents/harness/tools/inject-active-project-context.py`.

## Guardrails

- Prefer the helper script over manual YAML edits for deterministic changes.
- Use `python3` on this machine; `python` is not available.
- Keep `openspec_root`, repo `root`, and `follow_files` relative to the `agent-harness` root.
- Remove or avoid `follow_files` entries that do not exist, so profile validation stays clean.
- Remember that `.agents/harness/config/agent-harness.yaml` is session-local and gitignored.

## Validation

```bash
python3 .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py validate-profile --project-id my-project
python3 .agents/harness/tools/inject-active-project-context.py
```