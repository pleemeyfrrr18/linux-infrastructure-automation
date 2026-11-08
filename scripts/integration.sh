#!/usr/bin/env bash
# Ephemeral Linux CI stack. Requires free loopback ports 8000, 8080, 8081, 9090, 3000.
set -euo pipefail
cd "$(dirname "$0")/.."
# Unique projects ensure cleanup cannot target a previously deployed Compose project.
app_project="lia-ci-$(date +%s)-$$"
monitoring_project="${app_project}-mon"
export GRAFANA_ADMIN_PASSWORD=ci-only-password-not-a-real-secret
cleanup() {
  status=$?
  if (( status != 0 )); then
    mkdir -p artifacts/integration
    docker compose -p "$app_project" -f docker/app.compose.yaml logs --no-color > artifacts/integration/app.log 2>&1 || true
    docker compose -p "$monitoring_project" -f docker/monitoring.compose.yaml logs --no-color > artifacts/integration/monitoring.log 2>&1 || true
    cat artifacts/integration/app.log artifacts/integration/monitoring.log
  fi
  # Remove only the containers and volumes created for this unique test run.
  docker compose -p "$monitoring_project" -f docker/monitoring.compose.yaml down --volumes || true
  docker compose -p "$app_project" -f docker/app.compose.yaml down --volumes || true
  exit "$status"
}
trap cleanup EXIT
docker compose -p "$app_project" -f docker/app.compose.yaml up -d --build --wait --wait-timeout 120
scripts/smoke-test.sh http://127.0.0.1:8080
id="$(docker compose -p "$app_project" -f docker/app.compose.yaml ps -q app)"
[[ "$(docker inspect --format '{{.Config.User}}' "$id")" == '10001:10001' ]]
[[ "$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' "$id")" == true ]]
docker compose -p "$monitoring_project" -f docker/monitoring.compose.yaml up -d
python3 - <<'PYTHON'
import base64, json, time, urllib.request

def get(path, auth=False):
    req = urllib.request.Request(path)
    if auth:
        credentials = base64.b64encode(b'admin:ci-only-password-not-a-real-secret').decode()
        req.add_header('Authorization', 'Basic ' + credentials)
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)

for attempt in range(60):
    try:
        assert get('http://127.0.0.1:3000/api/health')['database'] == 'ok'
        assert get('http://127.0.0.1:3000/api/dashboards/uid/linux-infra', True)['dashboard']['uid'] == 'linux-infra'
        targets = get('http://127.0.0.1:9090/api/v1/targets')['data']['activeTargets']
        healthy = {t['labels']['job'] for t in targets if t['health'] == 'up'}
        # Native exporters are installed by Ansible on VMs, not in this CI stack.
        assert {'application', 'prometheus'} <= healthy
        break
    except Exception:
        if attempt == 59:
            raise
        time.sleep(2)
print('PASS: app proxy, container settings, Grafana dashboard and Prometheus app scrape')
PYTHON
