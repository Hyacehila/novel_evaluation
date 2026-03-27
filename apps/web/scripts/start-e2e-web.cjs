const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');

const webRoot = path.resolve(__dirname, '..');
const nextCacheDir = path.join(webRoot, '.next', 'cache');
fs.rmSync(nextCacheDir, { recursive: true, force: true });
const command = process.platform === 'win32' ? (process.env.ComSpec || 'cmd.exe') : 'sh';
const args = process.platform === 'win32'
  ? ['/d', '/s', '/c', 'pnpm build && pnpm start --hostname 127.0.0.1 --port 13000']
  : ['-lc', 'pnpm build && pnpm start --hostname 127.0.0.1 --port 13000'];

const child = spawn(
  command,
  args,
  {
    cwd: webRoot,
    stdio: 'inherit',
    env: {
      ...process.env,
      NOVEL_EVAL_API_HOST: '127.0.0.1',
      NOVEL_EVAL_API_PORT: '18000',
    },
  }
);

const forwardSignal = (signal) => {
  if (!child.killed) {
    child.kill(signal);
  }
};

process.on('SIGINT', () => forwardSignal('SIGINT'));
process.on('SIGTERM', () => forwardSignal('SIGTERM'));
child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
