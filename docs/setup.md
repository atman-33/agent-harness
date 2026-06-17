# agent-harness Setup Guide

This guide walks through setting up `agent-harness` on a new machine from scratch, including all MCP servers and project configuration.

## Prerequisites

Install the following tools before cloning the repository.

| Tool | Version | Purpose |
|------|---------|---------|
| Git | any | Repository cloning |
| Node.js | 22+ | MCP launchers and npm tools |
| Python | 3.11+ | Session hooks and uv/uvx tooling |
| uv | latest | Runs the serena MCP server via `uvx` |
| Claude Code CLI | latest | Primary AI coding interface |

### Install uv (Windows)

```powershell
winget install --id astral-sh.uv -e
```

Or with pip:

```powershell
pip install uv
```

### Install uv (WSL / Linux)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```powershell
uvx --version
```

For the full list of recommended local tools (zellij, rg, openspec, etc.), see [recommended-tool-installation.md](recommended-tool-installation.md).

---

## 1. Clone the Repository

```powershell
git clone <repository-url> agent-harness
cd agent-harness
```

---

## 2. Install MCP Server Dependencies

The repository ships three MCP servers configured in `.mcp.json`:

### memory

```powershell
npm install -g mcp-server-memory
```

### context7

The launcher (`tools/context7-mcp-launcher.js`) falls back to `npx` automatically, but a global install avoids the slow cold-start:

```powershell
npm install -g @upstash/context7-mcp
```

### serena

No separate install is needed. The launcher (`tools/serena-mcp-launcher.js`) uses `uvx` to fetch and run serena from GitHub. `uv` must be installed (see Prerequisites above).

---

## 3. Enable MCP Servers in Claude Code

Create `.claude/settings.local.json` at the repository root if it does not already exist:

```json
{
  "permissions": {
    "allow": []
  },
  "enabledMcpjsonServers": [
    "memory",
    "serena",
    "context7"
  ]
}
```

The `enabledMcpjsonServers` list must match the keys in `.mcp.json`.

---

## 4. Create the Harness Config File

`.agents/harness/config/agent-harness.yaml` is excluded from git (`.gitignore`), so you must create it manually on each machine.

```powershell
New-Item -ItemType Directory -Force .agents/harness/config
```

Create `.agents/harness/config/agent-harness.yaml`:

```yaml
version: 2

# Project ids to include in the active session context.
active_projects:
  - my-project

# OpenSpec source to use for the current session.
# mode: project -> use the selected active project's openspec/ directory.
#   project_id is required and must be listed in active_projects.
# mode: harness -> use agent-harness/openspec.
openspec:
  mode: project
  project_id: my-project
```

Replace `my-project` with the id of your actual project profile.

---

## 5. Create a Project Profile

Project profiles live in `.agents/harness/projects/` and are also excluded from git.
Use the template at `.agents/harness/projects/_template.yaml` as a starting point:

```powershell
Copy-Item .agents/harness/projects/_template.yaml .agents/harness/projects/my-project.yaml
```

Edit the copy to match your local paths. Paths are relative to the `agent-harness` root:

```yaml
id: my-project

openspec_root: ../my-project

repos:
  - id: app
    root: ../my-project
    follow_files:
      - ../my-project/AGENTS.md
    default_checks:
      - echo "add validation commands here"

summary: |
  Short description of this project.
```

---

## 6. Verify the Setup

Start Claude Code from the `agent-harness` directory:

```powershell
claude
```

Then run `/mcp` inside the session. All three servers should show a connected status:

```
memory    ✓ connected
serena    ✓ connected
context7  ✓ connected
```

If a server fails to connect, see the Troubleshooting section below.

---

## Troubleshooting

### serena: `Failed to reconnect to serena: -32000`

**Cause:** Python 3.12 for Windows has a bug in its OpenSSL build (`OPENSSL_Uplink: no OPENSSL_Applink`). The serena process crashes immediately after initialisation, which surfaces as a `-32000` JSON-RPC error in Claude Code.

**Fix:** The launcher (`tools/serena-mcp-launcher.js`) already pins `--python 3.11`. If you see this error after updating uv or changing the Python version:

1. Open `tools/serena-mcp-launcher.js`.
2. Find the `--python` argument in the Windows branch.
3. Make sure it reads `'3.11'`, not `'3.12'` or later.

```js
child = spawn(
  'uvx',
  [
    '--native-tls',
    '--python',
    '3.11',   // <-- must be 3.11, not 3.12
    '--from',
    'git+https://github.com/oraios/serena',
    ...
  ],
  ...
);
```

4. Run `/mcp` again in Claude Code to reconnect.

You can also test the launcher directly from the terminal to see the full error output:

```powershell
node tools/serena-mcp-launcher.js
```

A healthy startup ends with a line containing `MCP server lifetime setup complete`. The OpenSSL crash prints `OPENSSL_Uplink(...): no OPENSSL_Applink` instead.

### context7: connection error

Ensure `npm install -g @upstash/context7-mcp` has been run, or that `npx` can reach the npm registry. The launcher falls back to `npx` automatically, but network issues will cause a cold-start failure.

### memory: command not found

```powershell
npm install -g mcp-server-memory
```

### MCP servers not listed by `/mcp`

Check that `.claude/settings.local.json` exists at the repository root and contains the `enabledMcpjsonServers` array with all three server names.
