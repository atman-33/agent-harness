# agent-harness Setup Guide

> **The fastest path:** start Claude Code from this directory (`claude`) and run
> **`/setup-harness`**. That command checks prerequisites, installs the
> `atman-marketplace` plugins, enables the MCP servers, runs OpenSpec setup, and tells you
> the few interactive steps you still need to run by hand.
>
> This page is the reference for prerequisites and troubleshooting behind that command.

## Prerequisites

Install the following tools before cloning the repository.

| Tool | Version | Purpose |
|------|---------|---------|
| Git | any | Repository cloning |
| Node.js | 22+ | MCP launchers and npm tools |
| Python | 3.11 | Serena MCP server (must be 3.11, not 3.12+) |
| uv | latest | Runs the Serena MCP server via `uvx` |
| Claude Code CLI | latest | Primary AI coding interface |
| GitHub CLI (`gh`) | latest | Used by `/setup-all` to install recommended skills |

### Install uv (Windows)

```powershell
winget install --id astral-sh.uv -e
```

### Install uv (WSL / Linux)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```powershell
uvx --version
```

For the full list of recommended local tools (zellij, rg, openspec, etc.), see
[recommended-tool-installation.md](recommended-tool-installation.md).

## How MCP is wired

The Serena (code intelligence) and Context7 (library docs) MCP servers are **provided by
the `engineering` plugin** from `atman-marketplace` — there is no `.mcp.json` in this
repository. Installing that plugin (handled by `/setup-harness`) is what makes the servers
available; `.claude/settings.local.json` then enables them via:

```json
{
  "enabledMcpjsonServers": ["serena", "context7"]
}
```

The `.opencode/mcp/*.mjs` launchers in this repo are for OpenCode only and are not used by
Claude Code.

---

## Troubleshooting

### Serena: `Failed to reconnect to serena: -32000`

**Cause:** Python 3.12 for Windows has a bug in its OpenSSL build
(`OPENSSL_Uplink: no OPENSSL_Applink`). The Serena process crashes immediately after
initialisation, which surfaces as a `-32000` JSON-RPC error in Claude Code.

**Fix:** The engineering plugin's Serena launcher pins `--python 3.11` to work around this.
If you see this error after updating uv or changing the Python version, confirm the
`--python` argument still reads `'3.11'` (not `'3.12'` or later) in the launcher used by
your tool:

- Claude Code → the engineering plugin's launcher at
  `~/.claude/plugins/cache/atman-marketplace/engineering/<version>/mcp/serena-mcp-launcher.mjs`
- OpenCode → `.opencode/mcp/serena-mcp-launcher.mjs` in this repo

Then run `/mcp` again in Claude Code to reconnect. A healthy startup ends with a line
containing `MCP server lifetime setup complete`; the OpenSSL crash prints
`OPENSSL_Uplink(...): no OPENSSL_Applink` instead.

### context7: connection error

Ensure `npx` can reach the npm registry. The launcher falls back to `npx` automatically,
but network issues will cause a cold-start failure. A global install avoids the slow
cold-start:

```powershell
npm install -g @upstash/context7-mcp
```

### MCP servers not listed by `/mcp`

1. Confirm the `engineering` plugin is installed
   (`claude plugin install engineering@atman-marketplace --scope project`).
2. Check that `.claude/settings.local.json` exists at the repository root and its
   `enabledMcpjsonServers` array contains both `serena` and `context7`.
3. Restart / reload the session so newly installed plugins load.
