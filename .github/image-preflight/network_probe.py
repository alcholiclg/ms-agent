"""Probe public endpoints without registry credentials or remote writes."""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

endpoints = [
    ("npm", "https://registry.npmjs.org/pnpm", {200}),
    ("aliyun-pypi", "https://mirrors.aliyun.com/pypi/simple/uv/", {200}),
    ("aliyun-debian", "https://mirrors.aliyun.com/debian/dists/bookworm/Release", {200}),
    ("nodesource", "https://deb.nodesource.com/setup_22.x", {200}),
    ("acr-unauthenticated", "https://mshub-registry.cn-zhangjiakou.cr.aliyuncs.com/v2/", {200, 401}),
]
results = []
for name, url, accepted in endpoints:
    started = time.monotonic()
    result = {"name": name, "url": url}
    try:
        request = urllib.request.Request(url, method="GET" if name.startswith("acr") else "HEAD")
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
        result.update(status=status, ok=status in accepted)
    except urllib.error.HTTPError as exc:
        result.update(status=exc.code, ok=exc.code in accepted)
    except Exception as exc:
        result.update(error=str(exc), ok=False)
    result["seconds"] = round(time.monotonic() - started, 2)
    print(json.dumps(result), flush=True)
    results.append(result)

Path("preflight-results").mkdir(exist_ok=True)
Path("preflight-results/network.json").write_text(json.dumps(results, indent=2) + "\n")
raise SystemExit(0 if all(result["ok"] for result in results) else 1)
