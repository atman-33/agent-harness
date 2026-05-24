---
name: create-feature-branch
description: Creates a new feature branch from main after confirming the target feature and syncing the local branch. Use when the user wants to start a new feature branch, asks to create a branch for upcoming work, or mentions a branch name such as feature/<name>.
argument-hint: "What feature or branch name should this use?"
---

# Create Feature Branch

Create a new feature branch for the user's next task.

## Quick start

1. Ask what feature the branch should represent unless the user already gave a clear branch name.
2. Turn the answer into a short branch name such as `feature/<name>`.
3. Update the local `main` branch to the latest state.
4. Create the new feature branch from `main` and switch to it.

## Workflow

1. Confirm the branch target.
   - If the user gives a feature description, convert it to a concise kebab-case slug.
   - If the user gives an exact branch name, use it when it matches the repository convention.
   - If the repository uses a different prefix than `feature/`, follow that convention.
2. Sync `main`.
   - Switch to the local `main` branch.
   - Update it from the default remote with a non-interactive command.
3. Create the feature branch.
   - Create the branch from the updated `main` branch.
   - Switch to the new branch immediately.
4. Report the result.
   - Tell the user the final branch name.
   - Surface blockers such as uncommitted changes, missing remotes, or pull failures instead of guessing.

## Notes

- Use non-interactive git commands.
- Do not invent a branch name when the requested feature is still ambiguous.
- Only perform the git steps when the user has explicitly asked for branch creation.