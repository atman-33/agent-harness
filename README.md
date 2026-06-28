# agent-harness

A general-purpose AI agent harness for multi-repo development — launch Claude Code or OpenCode from a single directory and work across any number of sibling repositories via project profiles.

[![GitHub stars](https://img.shields.io/github/stars/atman-33/agent-harness.svg?style=flat-square)](https://github.com/atman-33/agent-harness/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/atman-33/agent-harness.svg?style=flat-square)](https://github.com/atman-33/agent-harness/issues)
[![Node.js](https://img.shields.io/badge/node-%3E%3D22-brightgreen?style=flat-square)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square)](https://www.python.org/)

## Overview

`agent-harness` is a coordination layer that sits alongside your development repositories. You start the AI coding session here and point it at whichever sibling repo you want to work on — the harness wires up memory, code intelligence, and library documentation automatically via three MCP servers.

It ships a named multi-agent team (Noctis, Ignis, Gladiolus, Prompto) that can run spec-driven delivery workflows end to end: propose a change, implement with TDD, review, verify manually, archive, and open a PR. You can also invoke agents individually for one-off tasks.

## Features

- **Two MCP servers** wired at startup: Serena code intelligence and Context7 library docs
- **Named agent team** with distinct roles: orchestrator, strategist, implementer, and recon
- **OpenSpec integration** — spec-driven planning and task tracking per project
- **Dual AI tool support** — works with Claude Code CLI and OpenCode

## Getting Started

> [!TIP]
> The quickest path is to start Claude Code from this directory and run **`/setup-harness`**.
> It automates steps 1–4 below (prerequisite checks, plugin install, MCP enablement, and
> OpenSpec setup) and walks you through the few interactive steps. See [docs/setup.md](docs/setup.md).

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Git | any | Repository cloning |
| Node.js | 22+ | MCP launchers and npm tools |
| Python | 3.11 | Serena MCP server (must be 3.11, not 3.12+) |
| uv | latest | Runs Serena via `uvx` |
| Claude Code CLI | latest | Primary AI coding interface |

Install `uv` on Windows:

```powershell
winget install --id astral-sh.uv -e
```

Install `uv` on WSL / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For the full list of recommended tools (`zellij`, `rg`, `openspec`, etc.), see [docs/recommended-tool-installation.md](docs/recommended-tool-installation.md).

### 1. Clone and install MCP servers

```powershell
git clone https://github.com/atman-33/agent-harness.git
cd agent-harness
```

Install the MCP servers used by the harness:

```powershell
npm install -g @upstash/context7-mcp
```

Serena runs via `uvx` automatically — no separate install needed.

### 2. Enable MCP servers in Claude Code

Create `.claude/settings.local.json` at the repository root:

```json
{
  "permissions": { "allow": [] },
  "enabledMcpjsonServers": ["serena", "context7"]
}
```

### 3. Verify the setup

```powershell
claude
```

Inside the session, run `/mcp`. Both servers should show connected:

```
serena    ✓ connected
context7  ✓ connected
```

### 4. Install recommended plugins

Two plugins from [atman-marketplace](https://github.com/atman-33/atman-marketplace) are recommended for this harness.

**Step 4a — Add the atman-marketplace:**

```bash
claude plugin marketplace add atman-33/atman-marketplace
```

**Step 4b — Install the `engineering` plugin at project scope:**

```bash
claude plugin install engineering@atman-marketplace --scope project
```

This ships the role-based sub-agents (Ignis, Gladiolus, Prompto, etc.) and git workflow skills used by the harness. Install at `project` scope so the team shares the same tooling.

**Step 4c — Install the `productivity` plugin at user scope:**

```bash
claude plugin install productivity@atman-marketplace --scope user
```

This provides productivity commands (`/create-readme`, `/create-claude-md`, and the skill installer) available across every project on your machine.

> [!TIP]
> `user` scope makes the plugin available in every Claude Code session across all projects — install once and forget about it. After installing, run `/install-recommended-skills` inside a session to bootstrap the rest of your skill setup in one step.

For the full list of available plugins and scopes, see the [atman-marketplace README](https://github.com/atman-33/atman-marketplace).

## Usage

### Running a delivery workflow

The agent team supports spec-driven delivery workflows end to end. For example, the `idea-to-openspec-dev` workflow runs the full cycle:

1. **spec** (Noctis) — clarifies the idea with you and creates OpenSpec artifacts
2. **implement** (Gladiolus) — implements with TDD in thin vertical slices
3. **review** (Ignis) — verifies implementation against specs and runs tests
4. **manual-verification** (Ignis) — guides you through a verification checklist
5. **archive** (Prompto) — archives the change and opens a PR

You can also invoke agents directly for ad-hoc work without a workflow.

## Repository Layout

```
agent-harness/
├── .github/
│   └── agents/                  # Agent persona definitions (Noctis, Ignis, Gladiolus, Prompto)
├── docs/
│   ├── setup.md                 # Full machine setup guide
│   └── recommended-tool-installation.md
└── openspec/                    # OpenSpec changes for the harness itself (git-ignored)
```

## Agent Team

The harness ships four named agents inspired by Final Fantasy XV, each with a defined role and session model:

| Agent | Role | Session | Persona |
|-------|------|---------|---------|
| **Noctis** | Orchestrator / executor | Persistent | Mission lead, blunt, laid-back |
| **Ignis** | Strategist / reviewer | Task-scoped | Analytical, perfectionist |
| **Gladiolus** | Implementer / guardian | Task-scoped | Straightforward, highest standards |
| **Prompto** | Recon / reporting | Task-scoped | Casual, fast, thorough |

Agent definitions live in `.github/agents/`. Noctis is the primary contact; the other three receive delegated tasks and report back via `send_report`.

## Troubleshooting

### Serena fails with an OpenSSL error

Python 3.12 for Windows has a known OpenSSL bug. The MCP launcher pins `--python 3.11` to work around it. If you see `-32000` errors after updating uv:

1. Open the Serena launcher: `.opencode/mcp/serena-mcp-launcher.mjs` for OpenCode, or the engineering plugin's launcher at `~/.claude/plugins/cache/atman-marketplace/engineering/<version>/mcp/serena-mcp-launcher.mjs` for Claude Code.
2. Confirm the `--python` argument reads `'3.11'`, not `'3.12'` or later.
3. Run `/mcp` in Claude Code to reconnect.

### MCP servers not listed by `/mcp`

Ensure `.claude/settings.local.json` exists at the repo root and contains both server names in `enabledMcpjsonServers`.

## Resources

- [Setup guide](docs/setup.md) — detailed step-by-step machine setup
- [Recommended tools](docs/recommended-tool-installation.md) — `zellij`, `rg`, `openspec`, and more
- [Claude Code CLI](https://claude.ai/code)
