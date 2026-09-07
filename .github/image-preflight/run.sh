#!/usr/bin/env bash
set -euo pipefail

mkdir -p preflight-results
probe_image="ms-agent-infra-probe:${GITHUB_SHA:-local}"
probe_container="ms-agent-infra-probe"
trap 'docker logs "$probe_container" > preflight-results/container.log 2>&1 || true; docker rm -f "$probe_container" >/dev/null 2>&1 || true' EXIT

started=$(date +%s)
docker buildx build --platform linux/amd64 --pull --no-cache --load \
  --progress plain --tag "$probe_image" \
  .github/image-preflight 2>&1 | tee preflight-results/build.log
finished=$(date +%s)
printf '%s\n' "$((finished - started))" > preflight-results/build-seconds.txt
docker image inspect "$probe_image" --format '{{json .}}' > preflight-results/image.json
docker run --detach --name "$probe_container" --publish 127.0.0.1:18080:8000 "$probe_image"

ready=false
for attempt in $(seq 1 30); do
  if curl --noproxy '*' --fail --silent --max-time 2 http://127.0.0.1:18080/api/health > preflight-results/health.json; then
    ready=true
    break
  fi
  if [ "$(docker inspect --format '{{.State.Running}}' "$probe_container")" != true ]; then
    break
  fi
  sleep 1
done
test "$ready" = true
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path('preflight-results/health.json').read_text())
assert data['ok'] and data['scope'] == 'infrastructure-only', data
assert data['node'].startswith('22.'), data
assert data['python']['version'].startswith('3.12.'), data
assert data['python']['httpx'] == '0.28.1', data
assert data['pnpmBuildVersion'] == '10.17.1', data
assert data['uv'].startswith('uv 0.12.8'), data
print(json.dumps(data, indent=2))
PY
docker stop --time 10 "$probe_container"
test "$(docker inspect --format '{{.State.ExitCode}}' "$probe_container")" = 0
df -h / > preflight-results/disk-after.txt
printf 'Infrastructure image built and smoke-tested locally; no registry push was performed.\n' >> "$GITHUB_STEP_SUMMARY"
