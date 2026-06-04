---
name: request-to-implementation
description: Orchestrates implementation from either a GitHub issue or the current conversation context through feature-branch creation, spec generation, TDD-based implementation, and repository-aware validation by delegating to the existing workflow assets in the resolved repository. Use when the user wants to start or continue implementation from an issue URL, a clarified feature request, or a conversation-derived plan.
argument-hint: "Provide the issue URL or the current request context, and optionally the target repository if it is not already clear."
---

# Request To Implementation

Drive implementation from either a GitHub issue or the current conversation context without copying the detailed instructions from the branching, spec, or TDD sources into this skill.

## Quick start

1. Determine whether the source of truth is a GitHub issue URL or the current conversation.
2. Gather the problem statement, scope, constraints, acceptance criteria, and repository hints from that source.
3. If the request context is still ambiguous, ask the user the minimum narrow question needed before proceeding.
4. Resolve the target repository and repository root from the source context and active project context.
5. Switch into the matching repository root and keep that repository context for git and implementation work.
6. Create or continue the feature branch by following the `create-feature-branch` skill.
7. Create or continue the spec artifacts by following the `openspec-ff-change` skill.
8. Implement the work by following the `tdd` skill.
9. Run repository-aware validation, including the repository's code-check commands when they exist.
10. When the changed slice has a realistic manual verification path, return concise user-facing verification steps after implementation so the user can check behavior immediately.

## Workflow

1. Gather the source request.
   - Accept either a full issue URL or the current conversation context as the implementation source.
   - For an issue source, read the issue title, description, acceptance criteria, and relevant comments.
   - For a conversation source, synthesize the user's stated goal, constraints, acceptance criteria, and non-goals from the conversation so far.
   - If the source is inaccessible, contradictory, or still too ambiguous to implement, stop and ask the user.

2. Normalize the implementation context.
   - Reduce the source into a concise implementation brief containing the problem, scope, constraints, acceptance criteria, and any explicit non-goals.
   - Prefer the user's latest explicit instruction when conversation context and linked issue context differ.
   - If acceptance criteria or repository context are still missing, ask the minimum narrow question needed before continuing.
   - Do not start branch, spec, or implementation work from a vague idea that has not yet been made implementation-ready.

3. Resolve the working repository.
   - Match the issue URL or request context to the repository in the active project.
   - Record the resolved repository id and repository root from `repos[].root`.
   - If more than one repository could apply, ask one narrow question before proceeding.
   - Switch into the matching repository root before any git command and keep it as the working directory from this point onward.

4. Create or continue the feature branch.
   - Derive a concise branch topic from the issue number and title when an issue exists, otherwise from the normalized request brief.
   - Hand off the branch step to the `create-feature-branch` skill together with the resolved repository context.
   - Keep that skill as the source of truth for naming, syncing `main`, and blocker handling.
   - If a matching branch already exists, continue it unless the user explicitly wants a fresh branch.
   - Do not invoke branch creation from the `agent-harness` repository root or any other unrelated repository.

5. Create or continue the spec artifacts.
   - Use the `openspec-ff-change` skill.
   - Feed it the normalized implementation brief and a change name derived from the issue or request.
   - Keep repository-specific commands and file edits in the same resolved repository root unless the workflow explicitly needs `agent-harness` for coordination files.
   - Follow that skill as written; do not restate or rewrite its detailed instructions here.
   - If a matching change already exists, continue it unless the user explicitly wants a fresh change.
   - If the skill needs a missing product decision, ask the user before inventing one.

6. Implement with TDD.
   - Use the resulting spec/tasks plus the normalized acceptance criteria to pick the first vertical slice.
   - Hand off the implementation loop to the `tdd` skill.
   - Keep the TDD skill as the source of truth for planning, red-green-refactor, and behavior-first tests.

7. Validate and report.
   - Run the repository's focused checks for the touched slice before widening scope.
   - Run repository-aware code checks from the resolved repository root after implementation.
   - Use `repos[].default_checks` from the resolved repo entry in the active context as the first source of truth for repository validation commands.
   - If `default_checks` are absent or do not include the repository's lint/check/static-analysis commands, inspect the resolved repository's documented scripts and instructions and run the relevant code-check commands that the repository actually defines.
   - Do not hardcode universal commands in this skill, and do not assume every repository uses `npm`.
   - If no repository-defined code-check command can be resolved confidently, report that gap instead of guessing.
   - When the changed slice can be checked manually in a realistic way, provide user-facing verification steps after implementation. Include prerequisites, exact commands or UI actions when needed, expected results, and any known caveats such as stale UI state or manual refresh requirements.
   - If no realistic manual verification path is available, say so briefly instead of inventing one.
   - Report the branch name, spec or change location, tests run, code checks run, any user-facing manual verification steps you provided, and any remaining blockers or open questions.

## Guardrails

- Do not duplicate or paraphrase the detailed instructions from `create-feature-branch`, `openspec-ff-change`, or `tdd`; refer to them and execute them.
- Do not create a branch, spec, or code change against the wrong repository just because the current editor focus is elsewhere.
- Do not hand off to `create-feature-branch` without passing the resolved repository context.
- Do not assume `repos[].default_checks` already cover lint/check commands when the resolved repository exposes additional repository-defined code checks.
- Do not invent validation commands that are not defined by the resolved repository's profile, scripts, or documented instructions.
- Do not invent manual verification steps that are not grounded in the changed code, acceptance criteria, repository scripts, or observable runtime surfaces.
- Do not dump generic smoke-test advice when the changed slice calls for targeted verification; keep user-facing verification steps specific to the implemented behavior.
- Do not treat a rough idea or partial conversation as implementation-ready when key constraints or acceptance criteria are still missing.
- If an issue URL or conversation request points outside the active project or does not contain enough context to proceed, ask the user instead of guessing.