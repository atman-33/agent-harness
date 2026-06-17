const { spawn } = require('node:child_process');

const isWin = process.platform === 'win32';

let child;
if (isWin) {
  child = spawn(
    'uvx',
    [
      '--native-tls',
      '--from',
      'git+https://github.com/oraios/serena',
      'serena',
      'start-mcp-server',
      '--open-web-dashboard',
      'false',
      '--context',
      'ide',
    ],
    { stdio: 'inherit' }
  );
} else {
  const cmd = [
    'uvx',
    '--from',
    'git+https://github.com/oraios/serena',
    'serena',
    'start-mcp-server',
    '--open-web-dashboard',
    'false',
    '--context',
    'ide',
  ].join(' ');
  child = spawn('/bin/bash', ['-l', '-c', cmd], { stdio: 'inherit' });
}

child.on('close', (code) => {
  process.exit(code ?? 0);
});
