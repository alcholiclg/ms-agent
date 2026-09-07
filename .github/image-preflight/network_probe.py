'''Probe public endpoints without registry credentials or remote writes.'''
import ipaddress
import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


def diagnose_acr():
    host = 'mshub-registry.cn-zhangjiakou.cr.aliyuncs.com'
    report = {'host': host, 'dns': [], 'tcp_ipv4': []}
    try:
        addresses = sorted({
            address[4][0]
            for address in socket.getaddrinfo(
                host, 443, type=socket.SOCK_STREAM)
        })
        report['dns'] = [{
            'address': address,
            'version': ipaddress.ip_address(address).version,
            'is_global': ipaddress.ip_address(address).is_global
        } for address in addresses]
        for address in [
                item for item in addresses
                if ipaddress.ip_address(item).version == 4
        ][:2]:
            started = time.monotonic()
            result = {'address': address, 'port': 443}
            try:
                with socket.create_connection((address, 443), timeout=5):
                    result['connected'] = True
            except OSError as exc:
                result.update(connected=False, error=str(exc))
            result['seconds'] = round(time.monotonic() - started, 2)
            report['tcp_ipv4'].append(result)
    except OSError as exc:
        report['dns_error'] = str(exc)

    try:
        response = subprocess.run([
            'curl', '--noproxy', '*', '--ipv4', '--connect-timeout', '8',
            '--max-time', '15', '--silent', '--show-error', '--output',
            '/dev/null', '--write-out', '%{json}', f'https://{host}/v2/'
        ],
                                  capture_output=True,
                                  text=True,
                                  timeout=20,
                                  check=False)
        stats = json.loads(response.stdout) if response.stdout else {}
        report['curl_ipv4'] = {
            'exit_code': response.returncode,
            'error': response.stderr.strip(),
            **{
                key: stats.get(key)
                for key in ('http_code', 'remote_ip', 'time_connect', 'time_appconnect', 'time_total')
            }
        }
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        report['curl_ipv4'] = {'error': str(exc)}
    Path('preflight-results/acr-diagnostics.json').write_text(
        json.dumps(report, indent=2) + '\n')
    print(json.dumps({'acr_diagnostics': report}), flush=True)


endpoints = [
    ('npm', 'https://registry.npmjs.org/pnpm', {200}),
    ('aliyun-pypi', 'https://mirrors.aliyun.com/pypi/simple/uv/', {200}),
    ('aliyun-debian',
     'https://mirrors.aliyun.com/debian/dists/bookworm/Release', {200}),
    ('nodesource', 'https://deb.nodesource.com/setup_22.x', {200}),
    ('acr-unauthenticated',
     'https://mshub-registry.cn-zhangjiakou.cr.aliyuncs.com/v2/', {200, 401}),
]
results = []
for name, url, accepted in endpoints:
    started = time.monotonic()
    result = {'name': name, 'url': url}
    try:
        request = urllib.request.Request(
            url, method='GET' if name.startswith('acr') else 'HEAD')
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
        result.update(status=status, ok=status in accepted)
    except urllib.error.HTTPError as exc:
        result.update(status=exc.code, ok=exc.code in accepted)
    except Exception as exc:
        result.update(error=str(exc), ok=False)
    result['seconds'] = round(time.monotonic() - started, 2)
    print(json.dumps(result), flush=True)
    results.append(result)

Path('preflight-results').mkdir(exist_ok=True)
Path('preflight-results/network.json').write_text(
    json.dumps(results, indent=2) + '\n')
if any(result['name'].startswith('acr') and not result['ok']
       for result in results):
    diagnose_acr()
raise SystemExit(0 if all(result['ok'] for result in results) else 1)
