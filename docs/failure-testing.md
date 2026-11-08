# Failure testing and recovery

The operator confirms a successful Node Exporter stop/start alert and recovery
experiment on app01; see [the evidence record](node-exporter-recovery.md).
The other scenarios below are planned, not reported as executed. Run disruptive
tests only after explicit approval, one at a time, on the lab. Keep console access. Record timestamps,
commands, actual output and recovery evidence using `incident-report.md`.

| Scenario | Action after approval | Expected result | Recovery / verification |
|---|---|---|---|
| Repeat configuration | `scripts/idempotency.sh` with sudo/vault flags | Second run has zero changes on both hosts | Investigate any changed task; never label it idempotent without output |
| Process crash | On app01, `sudo bash /path/to/restart-test.sh --confirm-failure-test` | RestartCount increases; proxy health recovers within 90 seconds | Inspect Compose logs and run smoke test |
| Manual container stop | On app01, `sudo docker compose -f app.compose.yaml stop app` in deployment docker directory | No automatic restart; application scrape fails, alert eventually fires | `sudo docker compose -f app.compose.yaml up -d --wait` |
| app01 shutdown | Shut down app01 using its console | Both app01 targets go down; TargetUnavailable becomes firing after the pending period | Start VM; verify Docker/exporter boot and all four targets return up |
| Broken Nginx configuration | Back up deployed config, introduce an invalid directive, restart nginx | Nginx fails; Docker retries; proxy target goes down | Re-run deploy.yml from unchanged repository to restore config |
| Service cannot start | Inspect the failed Nginx case via Compose status/logs | Failure visible in logs, failed target and alert | Correct config, rerun deployment, verify health |
| Rebuild | Prepare fresh VMs following deployment.md | Setup completes, dashboard and four targets work | Run smoke, verify and idempotency checks; record all prerequisites |

Commands in the table are examples for execution after approval, not a request
to run them now. Run Compose commands from `/opt/linux-infrastructure-automation/docker`.
The restart-test script needs copying to app01 if you want to use it there;
Ansible deliberately deploys only service artifacts, not failure-injection scripts.

## Restart semantics

The restart script kills the application process through its host PID, rather
than issuing `docker stop` or `docker kill`. Docker treats deliberate stops
specially and may suppress restart policies. The script requires elevated
access on app01 and verifies both restart count and recovered proxy health.
A fast crash/restart may happen between scrapes and never produce an alert;
that is expected. Use a deliberate stop for a sustained outage.

An unhealthy Docker status alone does not trigger an automatic restart. To
study health checks separately, observe their status and logs without assuming
an orchestrator exists. `depends_on: service_healthy` controls startup ordering,
not continuous repair of dependent services.

## Alert timing and evidence

Scrape and evaluation intervals are 15 seconds. TargetUnavailable has `for: 1m`;
allow about 60–90 seconds after the first failed scrape for it to fire. Resource
alerts require five minutes above threshold, and CPU uses a five-minute rate.
Inspect `/api/v1/targets`, `/api/v1/alerts`, `/alerts`, and Grafana panels.
Do not generate uncontrolled disk or memory pressure on small VMs simply to
obtain screenshots. Synthetic alert rule tests in CI are safer for thresholds.

Recovery should resolve the alert on a later evaluation. Capture the transition
from healthy → pending → firing → healthy. This is polling-based monitoring;
a short outage may be missed, and failure of mon01 itself cannot be reported
by that same unavailable Prometheus. There are no email/chat notifications.

## Reproducibility evidence

Keep one result record per meaningful experiment. Include image/package
versions, commit hash, VM addresses with secrets redacted, initial service state,
expected behavior, actual outputs, recovery time and unresolved issues.
Never present CI's ephemeral container checks as proof of deployment to VMs.

When sudo passwords differ, run the idempotency script separately with
`--limit app01` and `--limit mon01`, each with `--ask-become-pass --ask-vault-pass`.
The script compares the targeted host set across both runs and requires zero
changes on the second run. Save evidence from both hosts before claiming the
whole lab converges. Read-only `verify-server.sh` needs the Vault password for
Grafana API checks, but does not request sudo.
