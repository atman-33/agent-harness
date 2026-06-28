#!/usr/bin/env node
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const FORCE = process.argv.includes('--force');

const homeDir = os.homedir();
const claudePluginsRoot = process.env.CLAUDE_PLUGINS_ROOT || path.join(
  homeDir,
  '.claude',
  'plugins',
  'marketplaces'
);
const openCodeRoot = process.env.OPENCODE_GLOBAL_ROOT || path.join(homeDir, '.config', 'opencode');
const commandTargetRoot = path.join(openCodeRoot, 'command');
const skillTargetRoot = path.join(openCodeRoot, 'skills');

function logSection(label, items) {
  console.log(`\n## ${label}`);
  if (items.length === 0) {
    console.log('(none)');
    return;
  }

  for (const item of items) {
    console.log(`- ${item}`);
  }
}

function ensureDirectory(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function parsePluginList(output) {
  const lines = output.split(/\r?\n/);
  const plugins = [];
  const warnings = [];
  let current = null;

  for (const line of lines) {
    const pluginMatch = line.match(/^\s*❯\s+([^@\s]+)@([^\s]+)\s*$/u);
    if (pluginMatch) {
      if (current) {
        plugins.push(current);
      }

      current = {
        pluginName: pluginMatch[1],
        marketplace: pluginMatch[2],
        version: null,
        scope: null,
        status: null,
      };
      continue;
    }

    if (!current) {
      continue;
    }

    const versionMatch = line.match(/^\s*Version:\s+(.+)\s*$/);
    if (versionMatch) {
      current.version = versionMatch[1].trim();
      continue;
    }

    const scopeMatch = line.match(/^\s*Scope:\s+(.+)\s*$/);
    if (scopeMatch) {
      current.scope = scopeMatch[1].trim();
      continue;
    }

    const statusMatch = line.match(/^\s*Status:\s+(.+)\s*$/);
    if (statusMatch) {
      current.status = statusMatch[1].trim();
    }
  }

  if (current) {
    plugins.push(current);
  }

  for (const plugin of plugins) {
    if (!plugin.scope) {
      warnings.push(`Missing scope metadata for ${plugin.pluginName}@${plugin.marketplace}`);
    }
  }

  if (plugins.length === 0) {
    warnings.push('No plugin entries could be parsed from `claude plugin list`.');
  }

  return { plugins, warnings };
}

function copyCommandFiles(sourceRoot, pluginRef, copied, skipped, unavailable) {
  if (!fs.existsSync(sourceRoot)) {
    unavailable.push(`${pluginRef}/commands -> ${sourceRoot}`);
    return;
  }

  const entries = fs.readdirSync(sourceRoot, { withFileTypes: true })
    .filter((entry) => entry.isFile());

  if (entries.length === 0) {
    unavailable.push(`${pluginRef}/commands -> no files found`);
    return;
  }

  for (const entry of entries) {
    const sourcePath = path.join(sourceRoot, entry.name);
    const targetPath = path.join(commandTargetRoot, entry.name);

    if (fs.existsSync(targetPath) && !FORCE) {
      skipped.push(`command:${entry.name} (${pluginRef})`);
      continue;
    }

    fs.copyFileSync(sourcePath, targetPath);
    copied.push(`command:${entry.name} (${pluginRef})`);
  }
}

function copySkillDirs(sourceRoot, pluginRef, copied, skipped, unavailable) {
  if (!fs.existsSync(sourceRoot)) {
    unavailable.push(`${pluginRef}/skills -> ${sourceRoot}`);
    return;
  }

  const entries = fs.readdirSync(sourceRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory());

  if (entries.length === 0) {
    unavailable.push(`${pluginRef}/skills -> no directories found`);
    return;
  }

  for (const entry of entries) {
    const sourcePath = path.join(sourceRoot, entry.name);
    const targetPath = path.join(skillTargetRoot, entry.name);

    if (fs.existsSync(targetPath) && !FORCE) {
      skipped.push(`skill:${entry.name} (${pluginRef})`);
      continue;
    }

    if (fs.existsSync(targetPath) && FORCE) {
      fs.rmSync(targetPath, { recursive: true, force: true });
    }

    fs.cpSync(sourcePath, targetPath, { recursive: true, force: true });
    copied.push(`skill:${entry.name} (${pluginRef})`);
  }
}

let pluginListOutput;
try {
  pluginListOutput = execFileSync('claude', ['plugin', 'list'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
} catch (error) {
  const stderr = error.stderr ? String(error.stderr).trim() : '';
  const message = stderr || error.message;
  console.error(`Error: Failed to run \`claude plugin list\`: ${message}`);
  process.exit(1);
}

const { plugins, warnings } = parsePluginList(pluginListOutput);
const userScopePlugins = plugins.filter((plugin) => plugin.scope === 'user');

if (userScopePlugins.length === 0) {
  logSection('Parse warnings', warnings);
  console.log('\nNo user-scope Claude plugins found.');
  process.exit(0);
}

ensureDirectory(commandTargetRoot);
ensureDirectory(skillTargetRoot);

const copied = [];
const skipped = [];
const missing = [];
const unavailable = [];

for (const plugin of userScopePlugins) {
  const pluginRef = `${plugin.pluginName}@${plugin.marketplace}`;
  const pluginRoot = path.join(
    claudePluginsRoot,
    plugin.marketplace,
    'plugins',
    plugin.pluginName
  );

  if (!fs.existsSync(pluginRoot)) {
    missing.push(`${pluginRef} -> ${pluginRoot}`);
    continue;
  }

  copyCommandFiles(
    path.join(pluginRoot, 'commands'),
    pluginRef,
    copied,
    skipped,
    unavailable
  );
  copySkillDirs(
    path.join(pluginRoot, 'skills'),
    pluginRef,
    copied,
    skipped,
    unavailable
  );
}

logSection('User-scope plugins', userScopePlugins.map((plugin) => `${plugin.pluginName}@${plugin.marketplace}`));
logSection('Resolved paths', [
  `CLAUDE_PLUGINS_ROOT=${claudePluginsRoot}`,
  `OPENCODE_GLOBAL_ROOT=${openCodeRoot}`,
]);
logSection('Copied', copied);
logSection('Skipped (already exists)', skipped);
logSection('Missing plugin roots', missing);
logSection('Unavailable artifact directories', unavailable);
logSection('Parse warnings', warnings);

if (missing.length > 0 || warnings.length > 0) {
  process.exitCode = 2;
}