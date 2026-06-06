---
name: manage-agent-harness-projects
description: Manages agent-harness project configuration, including switching the active projects, choosing the active OpenSpec source, creating project profiles, and updating work-unit repository settings. Use when working in agent-harness on .agents/harness/config/agent-harness.yaml or .agents/harness/projects/*.yaml, or when the user asks to switch projects, add a project, or change openspec_root, repos[], follow_files, or default_checks.
compatibility: Requires Python with PyYAML.
---

Manage agent-harness project settings for work-unit based development.

## Quick start

- Switch the active project:
  `python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py set-active --project-id my-project --openspec-mode project --openspec-project-id my-project`
- Create a project profile:
  `python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py create-profile --project-id my-project --openspec-root ../my-project --summary "Short description" --repo-json '{"id":"app","root":"../my-project"}'`
- Validate a profile:
  `python .github/skills/manage-agent-harness-projects/scripts/manage_agent_harness_projects.py validate-profile --project-id my-project`

## Workflows

1. Read `.agents/harness/config/agent-harness.yaml` and the target file under `.agents/harness/projects/`.
2. Classify the task as one of these operations:
  - switch the active projects or OpenSpec source
   - create a new profile
   - update an existing profile
   - validate a profile
3. Prefer the helper script for deterministic operations:
   - `set-active`
   - `create-profile`
   - `update-profile`
   - `validate-profile`
4. Ask only for missing required fields:
   - `project_id`
   - `openspec_root`
   - at least one repo object with `id` and `root`
  - OpenSpec mode when the user cares whether OpenSpec should come from a project or from agent-harness itself
5. After every change, run `validate-profile` on the edited profile.
6. Summarize the resulting config and any validation warnings.

## Guardrails

- Treat all profile paths as relative to the agent-harness root.
- Do not edit target repository source files unless the user explicitly asks.
- Use `--allow-missing-paths` only when scaffolding a profile before the target repo exists.
- See [REFERENCE.md](REFERENCE.md) for command options and repo JSON examples.