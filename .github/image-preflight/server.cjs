const assert = require('node:assert');
const { execFileSync } = require('node:child_process');
const { readFileSync } = require('node:fs');
const http = require('node:http');

assert(require('is-number')(42));
const output = (file, args) => execFileSync(file, args, { encoding: 'utf8' }).trim();
const python = JSON.parse(output('python', ['-c',
  'import json, platform, httpx; print(json.dumps({"version": platform.python_version(), "httpx": httpx.__version__}))'
]));
const result = {
  ok: true,
  scope: 'infrastructure-only',
  node: process.versions.node,
  python,
  uv: output('uv', ['--version']),
  uvx: output('uvx', ['--version']),
  pnpmBuildVersion: readFileSync('pnpm-version.txt', 'utf8').trim(),
  npm: output('npm', ['--version']),
  git: output('git', ['--version'])
};
const server = http.createServer((request, response) => {
  response.writeHead(request.url === '/api/health' ? 200 : 404, { 'content-type': 'application/json' });
  response.end(JSON.stringify(result));
});
server.listen(8000, '0.0.0.0');
process.once('SIGTERM', () => server.close(() => process.exit(0)));
