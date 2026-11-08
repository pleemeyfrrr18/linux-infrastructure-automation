#!/usr/bin/env bash
# Opt-in failure injection. Run on app01 with authorized Docker access.
set -euo pipefail
[[ "${1:-}" == --confirm-failure-test ]] || {
  echo 'Usage: restart-test.sh --confirm-failure-test (kills app process on app01)' >&2; exit 2;
}
cd /opt/linux-infrastructure-automation/docker
id="$(docker compose -f app.compose.yaml ps -q app)"
[[ -n "$id" ]]
before="$(docker inspect --format '{{.RestartCount}}' "$id")"
# Kill host PID rather than docker stop/kill: Docker manual stops suppress restart policy.
pid="$(docker inspect --format '{{.State.Pid}}' "$id")"
kill -KILL "$pid"
for _ in {1..45}; do
  after="$(docker inspect --format '{{.RestartCount}}' "$id")"
  if (( after > before )) && curl -fsS http://127.0.0.1:8081/health >/dev/null; then
    echo "PASS: restart count $before -> $after; proxy health recovered"; exit 0
  fi
  sleep 2
done
echo 'FAIL: application did not recover within 90 seconds' >&2
exit 1
