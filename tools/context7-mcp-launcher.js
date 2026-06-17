const { spawn } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');

// Try global npm install path first (fast startup, no network needed)
const globalPath = path.join(
  process.env.APPDATA || require('os').homedir(),
  'npm',
  'node_modules',
  '@upstash',
  'context7-mcp',
  'dist',
  'index.js'
);

let child;
if (fs.existsSync(globalPath)) {
  child = spawn(process.execPath, [globalPath], { stdio: 'inherit' });
} else {
  // Fall back to npx (slower — run `npm install -g @upstash/context7-mcp` to avoid this)
  child = spawn('cmd', ['/c', 'npx', '-y', '@upstash/context7-mcp'], { stdio: 'inherit' });
}

child.on('close', (code) => process.exit(code ?? 0));
