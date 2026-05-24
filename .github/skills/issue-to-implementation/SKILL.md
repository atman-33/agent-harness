---
name: issue-to-implementation
description: Orchestrates issue-driven development from a GitHub issue URL through feature-branch creation, spec generation, TDD-based implementation, and repository-aware validation by delegating to the existing workflow assets in the resolved repository. Use when the user provides a development issue URL and wants the branch, spec, implementation, and follow-up validation flow started or continued end-to-end.
argument-hint: "Provide the development issue URL, and optionally the target repository if the URL alone is not enough."
---

# Issue To Implementation

Drive development from a GitHub issue URL without copying the detailed instructions from the branching, prompt, or TDD sources into this skill.

## Quick start

1. Get the issue URL from the user if it was not already provided.
2. Read the issue body and relevant recent comments.
3. Resolve the target repository and repository root from the issue URL and active project context.
4. Switch into the matching repository root and keep that repository context for git and implementation work.
5. Create or continue the feature branch by following the `create-feature-branch` skill.
6. Create or continue the spec artifacts by following the target repository's `.github/prompts/opsx-ff.prompt.md`.
7. Implement the work by following the `tdd` skill.
8. Run repository-aware validation, including the repository's code-check commands when they exist.

## Workflow

1. Gather the source issue.
   - Accept a full issue URL.
   - Read the issue title, description, acceptance criteria, and relevant comments.
   - If the issue is inaccessible or ambiguous, stop and ask the user.

2. Resolve the working repository.
   - Match the issue URL to the repository in the active project.
   - Record the resolved repository id and repository root from `repos[].root`.
   - If more than one repository could apply, ask one narrow question before proceeding.
   - Switch into the matching repository root before any git command and keep it as the working directory from this point onward.

3. Create or continue the feature branch.
   - Derive a concise branch topic from the issue number and title.
   - Hand off the branch step to the `create-feature-branch` skill together with the resolved repository context.
   - Keep that skill as the source of truth for naming, syncing `main`, and blocker handling.
   - If a matching branch already exists, continue it unless the user explicitly wants a fresh branch.
   - Do not invoke branch creation from the `agent-harness` repository root or any other unrelated repository.

4. Create or continue the spec artifacts.
   - Use the matching repository's `.github/prompts/opsx-ff.prompt.md`.
   - Feed it the issue context and a change name derived from the issue.
   - Keep repository-specific commands and file edits in the same resolved repository root unless the workflow explicitly needs `agent-harness` for coordination files.
   - Follow the prompt as written; do not restate or rewrite its detailed instructions here.
   - If a matching change already exists, continue it unless the user explicitly wants a fresh change.
   - If the prompt needs a missing product decision, ask the user before inventing one.

5. Implement with TDD.
   - Use the resulting spec/tasks plus the issue acceptance criteria to pick the first vertical slice.
   - Hand off the implementation loop to the `tdd` skill.
   - Keep the TDD skill as the source of truth for planning, red-green-refactor, and behavior-first tests.

6. Validate and report.
   - Run the repository's focused checks for the touched slice before widening scope.
   - Run repository-aware code checks from the resolved repository root after implementation.
   - Use `repos[].default_checks` from the active project profile as the first source of truth for repository validation commands.
   - If `default_checks` are absent or do not include the repository's lint/check/static-analysis commands, inspect the resolved repository's documented scripts and instructions and run the relevant code-check commands that the repository actually defines.
   - Do not hardcode universal commands in this skill, and do not assume every repository uses `npm`.
   - If no repository-defined code-check command can be resolved confidently, report that gap instead of guessing.
   - Report the branch name, spec or change location, tests run, code checks run, and any remaining blockers or open questions.

## Guardrails

- Do not duplicate or paraphrase the detailed instructions from `create-feature-branch`, `.github/prompts/opsx-ff.prompt.md`, or `tdd`; refer to them and execute them.
- Do not create a branch, spec, or code change against the wrong repository just because the current editor focus is elsewhere.
- Do not hand off to `create-feature-branch` without passing the resolved repository context.
- Do not assume `repos[].default_checks` already cover lint/check commands when the resolved repository exposes additional repository-defined code checks.
- Do not invent validation commands that are not defined by the resolved repository's profile, scripts, or documented instructions.
- Do not treat the issue title alone as sufficient when the body or comments materially change scope.
- If the issue URL points outside the active project or does not contain enough context to proceed, ask the user instead of guessing.