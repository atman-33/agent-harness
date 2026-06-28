---
name: handoff-go
description: Write a handoff document and launch the next agent in a split zellij pane, with new-window and paste-ready fallbacks when zellij is not in use.
argument-hint: What the next session should focus on (plus any extra instructions)
disable-model-invocation: true
---

Hand off the current conversation **and** start the next agent in one go: write the handoff document, then `dispatch.mjs` launches a fresh `claude` that reads it and continues. The baton leaves your hand and the next runner is already moving.

You write the document (judgment). `dispatch.mjs` owns the deterministic rest — environment detection, the initial prompt, the A→B→C fallback, and shell-safe launching.

## Step 1 — Write the handoff document

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save it to the OS temporary directory — not the workspace. Capture its **absolute path**.

- Include a "suggested skills" section listing skills the next agent should invoke.
- Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs); reference them by path or URL.
- Redact sensitive information (API keys, passwords, PII).
- Treat the skill arguments as a description of what the next session will focus on, and tailor the document to it.

Done when: the document is saved, its absolute path is captured, secrets are redacted, and a "suggested skills" section is present.

## Step 2 — Dispatch

Run the dispatcher from the skill directory:

```
node dispatch.mjs --doc "<absolute doc path>" --instructions "<the user's supplementary instructions from the arguments>"
```

Options: `--cwd <dir>` (working directory for the next agent; defaults to the current directory), `--layout pane|tab` (default `pane`), `--dry-run` (print what would run without launching).

The script detects the mode, composes the initial prompt, and launches with fallback:

| Mode | Condition | Action |
|------|-----------|--------|
| **A — in-session** | `$ZELLIJ` / `$ZELLIJ_SESSION_NAME` set (already inside zellij) | Split a pane (or new tab) running `claude` |
| **B — new window** | not in zellij, but `zellij` + a terminal launcher exist | Open a new terminal window hosting zellij + `claude` |
| **C — manual** | otherwise | Print a paste-ready `claude` command + the document path |

Done when: the script exits and reports the mode it used (A/B/C).

## Step 3 — Report the result

Tell the user which mode fired. For mode C (or any fallback), surface the script's paste-ready `claude` command and the document path verbatim so they can launch the next agent themselves.

Done when: the launch result — or the manual command for mode C — has been relayed to the user.
