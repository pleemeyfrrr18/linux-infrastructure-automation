#!/usr/bin/env bash
set -euo pipefail
base="${1:?Usage: smoke-test.sh http://APP_IP:8080}"
python3 - "$base" <<'PYTHON'
import json, sys, urllib.request
base = sys.argv[1].rstrip('/')
with urllib.request.urlopen(base + '/health', timeout=5) as r:
    assert r.status == 200 and json.load(r)['status'] == 'ok'
with urllib.request.urlopen(base + '/metrics', timeout=5) as r:
    assert 'demo_app_up 1' in r.read().decode()
print('PASS: proxy health and application metrics')
PYTHON
