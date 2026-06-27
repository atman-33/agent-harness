---
name: create-pull-request
description: Analyzes git changes, drafts localized PR titles and bodies, and assists with creating or updating GitHub pull requests for the active agent-harness project repository. Use when working from agent-harness and the user wants to create a PR, review branch changes, draft or update a PR description, or check whether a branch is ready for review.
compatibility: Requires git, GitHub CLI, and Python. PowerShell examples assume Windows.
---

# Create Pull Request

Creates reviewer-friendly PR drafts for a repository selected from the active agent-harness project.

## Quick start

1. Read `.agents/harness/config/agent-harness.yaml`, resolve `active_projects`, and inspect the active project profiles relevant to the task.
2. Pick the target repository using this order: the repo named by the user; otherwise the repo owning the current file if it is unambiguous; otherwise the only repo in the active context; otherwise ask.
3. Run git and gh commands in the target repository root, not in the `agent-harness` repository root.
4. Save generated analysis and PR body files only under `.github/skills/create-pull-request/temp-files/` in `agent-harness`.
5. Draft first and ask for approval before creating or updating the PR, unless the user explicitly asked for immediate creation.

## Workflow

1. Resolve the target repository path from the active context.
2. Use `Push-Location` / `Pop-Location` or an equivalent directory stack when switching into the target repository.
3. Run `scripts/analyze_changes.py` from the target repository to produce the analysis JSON.
4. Choose the PR template from `assets/templates/` based on branch intent, then run `scripts/generate_pr_body.py`.
5. Run `scripts/quality_checks.py` before presenting or creating the PR.
6. Present the draft and warnings to the user, or create or update the PR immediately if the user explicitly asked for that fast path.

## Guardrails

- Never run git or gh against the `agent-harness` repository unless the PR is intentionally for `agent-harness` itself.
- Keep all temporary PR artifacts inside `temp-files/` in this skill directory.
- Treat a requested output language as binding for the final PR title and body.
- Preserve issue references, but only emit closing keywords when the PR targets the repository default branch.
- See [REFERENCE.md](REFERENCE.md) for the full workflow, PowerShell examples, and error handling.
