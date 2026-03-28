const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');

const webRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(webRoot, '..', '..');
const providerMode = process.env.NOVEL_EVAL_E2E_PROVIDER_MODE ?? 'startup_key';
const artifactsDir = path.join(webRoot, '.playwright', providerMode);
const logsDir = path.join(artifactsDir, 'logs');
const dbPath = path.join(artifactsDir, 'e2e.sqlite3');

fs.mkdirSync(logsDir, { recursive: true });
fs.rmSync(dbPath, { force: true });

if (providerMode === 'startup_key' && !process.env.NOVEL_EVAL_DEEPSEEK_API_KEY) {
  console.error('NOVEL_EVAL_DEEPSEEK_API_KEY is required for startup_key Playwright E2E.');
  process.exit(1);
}

const childEnv = {
  ...process.env,
  PYTHONPATH: repoRoot,
  NOVEL_EVAL_DB_PATH: dbPath,
  NOVEL_EVAL_LOG_DIR: logsDir,
};
if (providerMode === 'runtime_key') {
  delete childEnv.NOVEL_EVAL_DEEPSEEK_API_KEY;
}

const uvCommand = process.platform === 'win32' ? 'uv.exe' : 'uv';
const child = spawn(
  uvCommand,
  ['run', '--project', 'apps/api', 'uvicorn', 'api.app:app', '--host', '127.0.0.1', '--port', '18000'],
  {
    cwd: repoRoot,
    stdio: 'inherit',
    env: childEnv,
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
