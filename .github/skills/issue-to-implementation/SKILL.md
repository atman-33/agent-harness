---
name: issue-to-implementation
description: Orchestrates issue-driven development from a GitHub issue URL through feature-branch creation, spec generation, and TDD-based implementation by delegating to the existing workflow assets. Use when the user provides a development issue URL and wants the branch, spec, and implementation flow started or continued end-to-end.
argument-hint: "Provide the development issue URL, and optionally the target repository if the URL alone is not enough."
---

# Issue To Implementation

Drive development from a GitHub issue URL without copying the detailed instructions from the branching, prompt, or TDD sources into this skill.

## Quick start

1. Get the issue URL from the user if it was not already provided.
2. Read the issue body and relevant recent comments.
3. Resolve the target repository from the issue URL and active project context.
4. Create or continue the feature branch by following the `create-feature-branch` skill.
5. Create or continue the spec artifacts by following the target repository's `.github/prompts/opsx-ff.prompt.md`.
6. Implement the work by following the `tdd` skill.

## Workflow

1. Gather the source issue.
   - Accept a full issue URL.
   - Read the issue title, description, acceptance criteria, and relevant comments.
   - If the issue is inaccessible or ambiguous, stop and ask the user.

2. Resolve the working repository.
   - Match the issue URL to the repository in the active project.
   - If more than one repository could apply, ask one narrow question before proceeding.
   - Work in the matching repository from this point onward.

3. Create or continue the feature branch.
   - Derive a concise branch topic from the issue number and title.
   - Hand off the branch step to the `create-feature-branch` skill.
   - Keep that skill as the source of truth for naming, syncing `main`, and blocker handling.
   - If a matching branch already exists, continue it unless the user explicitly wants a fresh branch.

4. Create or continue the spec artifacts.
   - Use the matching repository's `.github/prompts/opsx-ff.prompt.md`.
   - Feed it the issue context and a change name derived from the issue.
   - Follow the prompt as written; do not restate or rewrite its detailed instructions here.
   - If a matching change already exists, continue it unless the user explicitly wants a fresh change.
   - If the prompt needs a missing product decision, ask the user before inventing one.

5. Implement with TDD.
   - Use the resulting spec/tasks plus the issue acceptance criteria to pick the first vertical slice.
   - Hand off the implementation loop to the `tdd` skill.
   - Keep the TDD skill as the source of truth for planning, red-green-refactor, and behavior-first tests.

6. Validate and report.
   - Run the repository's focused checks for the touched slice before widening scope.
   - Report the branch name, spec or change location, tests run, and any remaining blockers or open questions.

## Guardrails

- Do not duplicate or paraphrase the detailed instructions from `create-feature-branch`, `.github/prompts/opsx-ff.prompt.md`, or `tdd`; refer to them and execute them.
- Do not create a branch, spec, or code change against the wrong repository just because the current editor focus is elsewhere.
- Do not treat the issue title alone as sufficient when the body or comments materially change scope.
- If the issue URL points outside the active project or does not contain enough context to proceed, ask the user instead of guessing.