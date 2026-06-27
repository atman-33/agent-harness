# Create Pull Request Reference

This reference expands the `create-pull-request` workflow for `agent-harness`.

## Core philosophy

- Default to human-in-the-loop. Prepare a draft, show it to the user, and ask for approval before creating or updating the PR.
- If the user explicitly asks for immediate PR creation, you may generate the draft, run sanity checks, summarize the result, and create or update the PR without another approval turn.
- If the user requests a language, the final PR title and body must be written in that language.

## Resolve the target repository

1. Read `.agents/harness/config/agent-harness.yaml`.
2. Resolve `active_projects`.
3. Read the relevant profiles under `.agents/harness/projects/`.
4. Choose the target repo using this order: the repo named by the user; otherwise the repo owning the current file if it is unambiguous; otherwise the only repo in the active context; otherwise ask.

PowerShell example:

```powershell
$HarnessRoot = "C:\repos\agent-harness"
$TargetRepo = "C:\repos\multi-agent-ff15-vscode"
```

All git and `gh` commands must run in `$TargetRepo`.

## Analyze changes

Gather the branch context first:

```powershell
$HarnessRoot = "C:\repos\agent-harness"
$TargetRepo = "C:\repos\multi-agent-ff15-vscode"
$TempRoot = Join-Path $HarnessRoot ".github\skills\create-pull-request\temp-files"
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

Push-Location $TargetRepo

$CurrentBranch = git branch --show-current
$TargetBranch = if ($env:TARGET_BRANCH) { $env:TARGET_BRANCH } else { "main" }
$BranchSlug = (($CurrentBranch -replace "/", "-") -replace "[^A-Za-z0-9._-]", "-").Trim("-")
if ([string]::IsNullOrWhiteSpace($BranchSlug)) { $BranchSlug = "head" }
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

$AnalysisFile = Join-Path $TempRoot ("pr-analysis-{0}-{1}.json" -f $BranchSlug, $Stamp)
$PrBodyFile = Join-Path $TempRoot ("pr-body-{0}-{1}.md" -f $BranchSlug, $Stamp)

git diff "$TargetBranch...HEAD" --stat
git log "$TargetBranch..HEAD" --oneline
git diff "$TargetBranch...HEAD" --name-status

python "$HarnessRoot\.github\skills\create-pull-request\scripts\analyze_changes.py" "$TargetBranch" --output "$AnalysisFile"
```

Use the analysis JSON as the source of truth for diff stats, category summaries, commit themes, and issue references.

## Determine PR type

Prefer the branch name first:

- `feature/*` or `feat/*` -> feature template
- `bugfix/*`, `fix/*`, or `hotfix/*` -> bugfix template
- `docs/*` -> docs template
- `refactor/*` -> refactor style body using the feature template unless a dedicated template is added later
- `chore/*`, `build/*`, or `ci/*` -> chore style body using the feature template unless a dedicated template is added later
- anything else -> feature template by default

If the branch name is inconclusive, use commit prefixes and the change mix. Do not switch to a bugfix template just because a feature branch contains one `fix:` commit.

## Generate the PR draft

Templates live under `assets/templates/`.

Examples:

- `assets/templates/pr-template-feature.md`
- `assets/templates/pr-template-feature-ja.md`
- `assets/templates/pr-template-bugfix.md`
- `assets/templates/pr-template-docs.md`

PowerShell example:

```powershell
$TemplateFile = "$HarnessRoot\.github\skills\create-pull-request\assets\templates\pr-template-feature-ja.md"

python "$HarnessRoot\.github\skills\create-pull-request\scripts\generate_pr_body.py" `
  "$TemplateFile" `
  "$AnalysisFile" `
  "$PrBodyFile" `
  --language ja
```

Auto-filled sections should cover:

- summary from commit themes
- change breakdown from diff stats and category or top-level area summaries
- related issues, preserving closing vs non-closing intent
- checklist items based on change types

If classification confidence is low, prefer diff stats and top-level directories over forced category prose.

## Quality checks

Run the cross-platform checker before presenting or creating the PR:

```powershell
python "$HarnessRoot\.github\skills\create-pull-request\scripts\quality_checks.py" "$TargetBranch"
```

The checker reports:

- uncommitted changes
- merge conflicts against the target branch
- whether the branch is actually ahead of the target branch
- TODO or FIXME comments in changed code files
- newly changed large files over 1 MiB
- missing test file changes when code changed
- dependency file changes

Warnings do not block PR creation by default. Hard failures should be surfaced to the user before creation.

## Present the draft

Default flow:

1. Show the generated PR title and body.
2. Call out any warnings or hard failures from quality checks.
3. Explicitly mention any closing keywords that will auto-close issues on merge.
4. Ask whether to create the PR, edit the body, change the base branch, or add reviewers.

If the user asked for immediate creation, summarize the draft briefly and proceed.

## Create or update the PR

Still inside the target repository:

```powershell
git push -u origin "$CurrentBranch"

$ExistingPr = gh pr list --head "$CurrentBranch" --state open --json number --jq '.[0].number'

if ($ExistingPr) {
  gh pr edit "$ExistingPr" --title "PR Title" --body-file "$PrBodyFile"
} else {
  gh pr create --title "PR Title" --body-file "$PrBodyFile" --base "$TargetBranch" --head "$CurrentBranch"
}

Pop-Location
```

Only suggest reviewers or labels when repository conventions are obvious or the user explicitly asks.

## Interactive editing loop

If the user wants changes:

1. Ask which section to modify.
2. Update only that section.
3. Re-present the full draft.
4. Repeat until approved.

## Error handling

- No commits ahead of target branch: tell the user there is nothing to PR yet.
- Merge conflicts: show the conflict risk and stop short of PR creation unless the user says otherwise.
- No GitHub CLI: offer to keep the generated PR body for manual submission.
- API or auth failures: surface the exact blocker and keep the draft files in `temp-files/`.
- Requested language not directly supported by a template: use the closest template, then rewrite the final title and body into the requested language.

## Supporting reference

See [references/pr-best-practices.md](references/pr-best-practices.md) for reviewer-facing writing guidance.