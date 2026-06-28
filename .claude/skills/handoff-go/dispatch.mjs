#!/usr/bin/env node
// handoff-go dispatcher: detect the environment, compose the next agent's
// initial prompt, and launch a fresh `claude` that continues from a handoff
// document. Deterministic half of the skill — keeps the branchy detection,
// fallback chain, and shell quoting out of the stochastic (LLM) layer.
//
// Usage:
//   node dispatch.mjs --doc <abs path> --instructions <text> [--cwd <dir>]
//                     [--layout pane|tab] [--dry-run]
//
// Modes (auto-detected, with fallback A -> C and B -> C):
//   A in-session : already inside zellij  -> split a pane (or new tab) running claude
//   B new-window : zellij + a terminal    -> open a new terminal hosting zellij + claude
//   C manual     : neither                -> print a paste-ready `claude` command

import { spawnSync } from 'node:child_process';
import os from 'node:os';
import fs from 'node:fs';
import path from 'node:path';

function parseArgs(argv) {
  const args = { layout: 'pane', dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case '--doc': args.doc = argv[++i]; break;
      case '--instructions': args.instructions = argv[++i]; break;
      case '--cwd': args.cwd = argv[++i]; break;
      case '--layout': args.layout = argv[++i]; break;
      case '--dry-run': args.dryRun = true; break;
      default:
        console.error(`Unknown argument: ${a}`);
        process.exit(2);
    }
  }
  return args;
}

function onPath(cmd) {
  const probe = process.platform === 'win32'
    ? spawnSync('where', [cmd], { stdio: 'ignore' })
    : spawnSync('which', [cmd], { stdio: 'ignore' });
  return probe.status === 0;
}

function insideZellij() {
  return Boolean(process.env.ZELLIJ || process.env.ZELLIJ_SESSION_NAME);
}

// Pick a terminal launcher for mode B. Returns a function (cmd, args) => spawnSync result, or null.
function terminalLauncher() {
  if (process.platform === 'win32') {
    if (onPath('wt')) {
      return (cmd, cmdArgs) => spawnSync('wt', ['new-tab', '--', cmd, ...cmdArgs], { stdio: 'inherit' });
    }
    return null;
  }
  const term = process.env.TERMINAL;
  const candidates = [term, 'x-terminal-emulator', 'gnome-terminal', 'konsole', 'kitty', 'alacritty', 'wezterm', 'xterm'].filter(Boolean);
  for (const t of candidates) {
    if (onPath(t)) {
      return (cmd, cmdArgs) => spawnSync(t, ['-e', cmd, ...cmdArgs], { stdio: 'inherit' });
    }
  }
  return null;
}

function buildPrompt({ doc, instructions }) {
  const extra = (instructions && instructions.trim()) ? `\n\nAdditional instructions: ${instructions.trim()}` : '';
  return `Read the handoff document at ${doc} and continue the work it describes. `
    + `Invoke the skills listed in its "suggested skills" section.${extra}`;
}

// A new pane (or tab) inside the current zellij session running claude.
function dispatchInSession({ cwd, layout, prompt, dryRun }) {
  const base = ['run', '--cwd', cwd];
  let argv;
  if (layout === 'tab') {
    if (!dryRun) spawnSync('zellij', ['action', 'new-tab', '--name', 'handoff-go'], { stdio: 'inherit' });
    argv = [...base, '--in-place', '--', 'claude', prompt];
  } else {
    argv = [...base, '--direction', 'right', '--', 'claude', prompt];
  }
  if (dryRun) { logCmd('zellij', argv); return 0; }
  return spawnSync('zellij', argv, { stdio: 'inherit' }).status ?? 1;
}

// A new terminal window hosting a one-pane zellij session running claude.
function dispatchNewWindow({ cwd, prompt, dryRun }) {
  const launch = terminalLauncher();
  if (!launch) return 1; // no launcher -> caller falls back to C
  const layoutFile = writeLayout({ cwd, prompt });
  const zellijArgs = ['--layout', layoutFile];
  if (dryRun) { logCmd('<terminal>', ['zellij', ...zellijArgs]); return 0; }
  return launch('zellij', zellijArgs).status ?? 1;
}

// Generate a temp KDL layout whose single pane runs claude with the prompt.
// A layout file sidesteps cross-process command quoting.
function writeLayout({ cwd, prompt }) {
  const esc = (s) => String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  const kdl = `layout {\n    pane cwd="${esc(cwd)}" {\n        command "claude"\n        args "${esc(prompt)}"\n    }\n}\n`;
  const file = path.join(os.tmpdir(), `handoff-go-${Date.now()}.kdl`);
  fs.writeFileSync(file, kdl, 'utf8');
  return file;
}

function logCmd(cmd, argv) {
  console.log(`[dry-run] ${cmd} ${argv.map((a) => (/\s/.test(a) ? JSON.stringify(a) : a)).join(' ')}`);
}

// Mode C: never fail — print a paste-ready command and the document path.
function dispatchManual({ doc, prompt }) {
  console.log('\nzellij not in use — run the next agent manually:\n');
  console.log(`  claude ${JSON.stringify(prompt)}\n`);
  console.log(`Handoff document: ${doc}`);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.doc) {
    console.error('Error: --doc <absolute path> is required');
    process.exit(2);
  }
  const cwd = args.cwd || process.cwd();
  const prompt = buildPrompt(args);

  // A: inside zellij
  if (insideZellij()) {
    const code = dispatchInSession({ cwd, layout: args.layout, prompt, dryRun: args.dryRun });
    if (code === 0) {
      console.log(`Dispatched (mode A, ${args.layout}) into the current zellij session.`);
      return;
    }
    console.error('Mode A failed; falling back to manual command.');
    dispatchManual({ doc: args.doc, prompt });
    return;
  }

  // B: zellij available + a terminal launcher
  if (onPath('zellij') && terminalLauncher()) {
    const code = dispatchNewWindow({ cwd, prompt, dryRun: args.dryRun });
    if (code === 0) {
      console.log('Dispatched (mode B) into a new terminal window.');
      return;
    }
    console.error('Mode B failed; falling back to manual command.');
  }

  // C: manual fallback
  dispatchManual({ doc: args.doc, prompt });
}

main();
