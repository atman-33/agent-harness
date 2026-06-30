---
description: First-time agent-harness setup — checks prerequisites, installs the atman-marketplace plugins (engineering/productivity), enables Serena & Context7 MCP, runs engineering /setup-all, runs productivity plugin setup (/install-recommended-skills, /setup-zellij-autostart), and verifies the session.
argument-hint: ""
allowed-tools: Bash Read Write Edit SlashCommand
---

# Setup agent-harness (first-time)

Bootstrap a fresh machine to use `agent-harness`. Run the **safe, idempotent** steps
automatically; for **interactive or system-level** steps (winget installs, `claude plugin`,
`gh auth`, `/mcp`), print the exact command and let the user run it.

Process the phases below in order. **A failure in one phase is reported, then the next
phase continues** — never abort the whole run on a single failure. Track each phase's
outcome (✓ done / ✗ failed / ⏭ skipped or manual) for the final summary table.

---

## Phase 0 — Detect environment (auto)

Determine whether this session is on **Windows (win32)** or **WSL/Linux**, and use the
matching command syntax for everything that follows:

- Windows → `winget` for system tools, PowerShell snippets.
- WSL/Linux → `apt` / `curl` for system tools, bash snippets.

State the detected environment once at the top of your output.

---

## Phase 1 — Prerequisite check (auto, read-only)

Probe each tool's version. Do **not** auto-install system tools — only report and, for
anything missing or too old, print the install command for the detected environment.

Run (skip gracefully if a command is absent):

```bash
git --version
node --version          # need >= 22
python --version        # need 3.11 (3.12+ breaks Serena's OpenSSL on Windows)
uvx --version           # uv must be installed; runs Serena
gh --version            # GitHub CLI; needed for `gh skill` in /setup-all
claude --version
```

Required minimums: **Node >= 22**, **Python 3.11**, plus `git`, `uv`, `claude`. `gh` is
needed only for the recommended-skills step.

Install hints to print for anything missing:

- **uv** — Windows: `winget install --id astral-sh.uv -e` · WSL/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **gh** — Windows: `winget install --id GitHub.cli -e` · WSL/Linux: `sudo apt install gh`
- **Node 22+ / Python 3.11** — see `docs/recommended-tool-installation.md`.

---

## Phase 2 — Recommended local tools (manual, optional)

These improve the workflow but are not strictly required. List which are already present
(reuse Phase 1 probes plus `zellij --version`, `rg --version`, `openspec --version`).
For the full per-OS install commands, point the user to
`docs/recommended-tool-installation.md` rather than duplicating the long lists here:
`zellij`, `rg`, `openspec`, `powershell-yaml`, GitHub Copilot CLI.

You **may** offer to auto-run the npm-based one if Node is present:

```bash
npm install -g @fission-ai/openspec@latest
```

Only run it after confirming; everything else is manual.

---

## Phase 3 — Marketplace + plugins (manual)

Three steps are required in order. `claude plugin` commands need a session reload to take
effect, so present all of them for the user to run at the shell (do not run them via Bash):

1. **Add the marketplace** — registers `atman-33/atman-marketplace` as a plugin source so
   `claude plugin install` can resolve packages from it.
2. **Install the engineering plugin** (project scope) → Serena + Context7 MCP, agent team,
   and skills.
3. **Install the productivity plugin** (user scope) → cross-project productivity commands.

```bash
claude plugin marketplace add atman-33/atman-marketplace
claude plugin install engineering@atman-marketplace --scope project
claude plugin install productivity@atman-marketplace --scope user
```

Tell the user to restart / reload the session after installing so the plugins load.

---

## Phase 4 — Enable MCP servers (auto, idempotent)

Ensure Claude Code will load the MCP servers shipped by the engineering plugin.

1. Read `.claude/settings.local.json` (create a minimal one if absent). **Merge** —
   never overwrite existing keys — so that `enabledMcpjsonServers` contains both
   `"serena"` and `"context7"`, and `permissions.allow` is preserved as-is.
2. Read `.claude/settings.json` and confirm
   `enabledPlugins["engineering@atman-marketplace"]` is `true` (leave other entries
   untouched). If the engineering plugin is not yet installed (Phase 3 pending), note
   that this takes effect once it is.

Minimal `settings.local.json` shape when creating from scratch:

```json
{
  "permissions": { "allow": [] },
  "enabledMcpjsonServers": ["serena", "context7"]
}
```

Show a diff/summary of what changed.

---

## Phase 5 — Run engineering /setup-all (auto if available)

If the engineering plugin is installed, invoke `/setup-all` via the SlashCommand tool.
It runs three sub-steps: install recommended skills, set up OpenSpec (`openspec init`),
and scaffold `.claude/project-context.json`.

- The recommended-skills step uses `gh skill`, which requires authentication. If
  `gh auth status` fails, tell the user to run `gh auth login` first, then re-run.
- If the engineering plugin is **not** installed yet, skip this phase and instruct the
  user to run `/setup-harness` again (or `/setup-all` directly) after completing Phase 3.

---

## Phase 6 — Productivity plugin setup (auto)

Run the two productivity sub-commands in order **only if the productivity plugin was
installed in Phase 3** (check `.claude/settings.json` for
`enabledPlugins["productivity@atman-marketplace"] === true`).

### 6-A — Install recommended skills (auto)

Invoke `/install-recommended-skills` via the SlashCommand tool. This installs
`grill-me`, `handoff`, and `writing-great-skills` at user scope via `gh skill install`.

- Requires `gh` to be authenticated. If `gh auth status` fails (already checked in
  Phase 1), skip 6-A and remind the user to run `gh auth login` first.
- If the productivity plugin is not yet installed, skip and instruct the user to run
  `/setup-harness` again after completing Phase 3.

### 6-B — Zellij autostart (auto)

Invoke `/setup-zellij-autostart` via the SlashCommand tool. It configures
PowerShell 7, Windows PowerShell, WSL bash, and WSL zsh profiles to auto-launch
Zellij on startup (idempotent — skips profiles that are already configured or where
Zellij is not installed).

---

## Phase 7 — Register sibling repositories (manual)

Open `.claude/project-context.json`.

- If it already exists, show its current `projects` entries and note it was left as-is.
- Otherwise (just scaffolded in Phase 5), guide the user to add each target sibling repo
  with an **absolute path** (Windows: `C:/repos/...`, WSL: `/mnt/c/repos/...`) and a short
  `summary`. Set `openspecPath` to the OpenSpec docs folder you want active.

Remind the user that changes to `project-context.json` take effect on the **next session
start**.

---

## Phase 8 — Verify (manual)

Ask the user to run `/mcp` inside the session and confirm:

```
serena    ✓ connected
context7  ✓ connected
```

If Serena fails with `-32000` / an OpenSSL error, the launcher's Python must be pinned to
**3.11** (Windows Python 3.12+ has an OpenSSL bug). See the Troubleshooting section of
`docs/setup.md`.

---

## Output Format

End every run with:

1. A status table:

   | Phase | Status | Notes |
   |-------|--------|-------|
   | 0 — Environment | ✓ | win32 / WSL |
   | 1 — Prerequisites | ✓ / ✗ | list missing tools |
   | 2 — Recommended tools | ✓ / ⏭ | present / pointed to docs |
   | 3 — Marketplace + plugins | ⏭ | manual — list commands |
   | 4 — Enable MCP | ✓ / ✗ | created / merged / unchanged |
   | 5 — /setup-all | ✓ / ⏭ | ran / pending plugin install |
   | 6-A — Install skills | ✓ / ✗ / ⏭ | installed / gh auth needed / plugin pending |
   | 6-B — Zellij autostart | ✓ / ⏭ | configured / zellij not installed |
   | 7 — Register projects | ✓ / ⏭ | edited / already configured |
   | 8 — Verify | ⏭ | manual — run /mcp |

2. **Next steps** — the exact commands the user still has to run by hand (plugin install,
   `gh auth login`, `/mcp`, editing `project-context.json`).

3. **Troubleshooting** — point to `docs/setup.md`.
