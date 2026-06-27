#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const FORCE = process.argv.includes('--force');

const cwd = process.cwd();
const settingsPath = path.join(cwd, '.claude', 'settings.json');
const targetRoot = path.join(cwd, '.opencode', 'skills');

function logSection(label, items) {
  console.log(`\n## ${label}`);
  if (items.length === 0) {
    console.log('(none)');
  } else {
    for (const item of items) {
      console.log(`- ${item}`);
    }
  }
}

if (!fs.existsSync(settingsPath)) {
  console.error(`Error: Project .claude/settings.json not found at ${settingsPath}`);
  process.exit(1);
}

let settings;
try {
  settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
} catch (err) {
  console.error(`Error: Failed to parse ${settingsPath}: ${err.message}`);
  process.exit(1);
}

const enabledPlugins = Object.entries(settings.enabledPlugins ?? {})
  .filter(([, value]) => value === true)
  .map(([key]) => key);

if (enabledPlugins.length === 0) {
  console.log(`No enabled plugins found in ${settingsPath}`);
  process.exit(0);
}

fs.mkdirSync(targetRoot, { recursive: true });

const copied = [];
const skipped = [];
const missing = [];

for (const pluginRef of enabledPlugins) {
  const match = pluginRef.match(/^([^@]+)@(.+)$/);
  if (!match) {
    console.warn(`Warning: Skipping malformed plugin reference: ${pluginRef}`);
    continue;
  }

  const [, pluginName, marketplace] = match;
  const sourceRoot = path.join(
    os.homedir(),
    '.claude',
    'plugins',
    'marketplaces',
    marketplace,
    'plugins',
    pluginName,
    'skills'
  );

  if (!fs.existsSync(sourceRoot)) {
    missing.push(`${pluginRef} -> ${sourceRoot}`);
    continue;
  }

  const skillDirs = fs.readdirSync(sourceRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);

  for (const skillName of skillDirs) {
    const sourceDir = path.join(sourceRoot, skillName);
    const targetDir = path.join(targetRoot, skillName);

    if (fs.existsSync(targetDir) && !FORCE) {
      skipped.push(skillName);
      continue;
    }

    if (fs.existsSync(targetDir) && FORCE) {
      fs.rmSync(targetDir, { recursive: true, force: true });
    }

    fs.cpSync(sourceDir, targetDir, { recursive: true, force: true });
    copied.push(`${pluginRef}/${skillName}`);
  }
}

logSection('Copied', copied);
logSection('Skipped (already exists)', skipped);
logSection('Missing source directories', missing);

if (missing.length > 0) {
  process.exitCode = 2;
}
