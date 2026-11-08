# Node Exporter alert and recovery record

Report recorded: **2026-11-08** (Asia/Qyzylorda). The original execution time was
not provided. Evidence sources: the operator's confirmation and four original
[screenshots](screenshots/README.md) supplied on 2026-11-08. No terminal transcript
or measured recovery timeline is saved.

## Confirmed report

| Item | Available evidence |
|---|---|
| Baseline | Operator confirms deployed app01 application stack and mon01 monitoring stack |
| Failure action | Node Exporter on app01 was stopped |
| Detection | [Firing capture](screenshots/01-alert-firing.png): TargetUnavailable, node/app01, critical, value 0 |
| Recovery action | Node Exporter on app01 was restarted |
| Recovery result | [Recovery capture](screenshots/02-alert-recovered.png): TargetUnavailable inactive; [targets capture](screenshots/04-prometheus-targets.png): all four targets UP |

The firing capture shows `alertname="TargetUnavailable"`, `instance="app01"`,
`job="node"` and `severity="critical"`, with state FIRING and value 0. The
post-incident capture shows the same rule inactive. The configured `up == 0`
expression and `for: 1m` pending period are visible. These screenshots support
alert detection and resolution; the exact service commands, original timestamps
and end-to-end recovery duration remain unrecorded.
Do not infer that the whole app01 VM or Python application was unavailable:
stopping the exporter affects host-metric collection, not those services directly.

## Repeatable procedure for a future approved test

These are suggested reproduction commands, not a transcript of the previous test.
They change a real service and must not run without approval. Keep a working SSH
session and verify the current baseline first.

1. Open the monitoring SSH tunnel from deployment.md. Check four healthy targets
   and record the initial `/api/v1/alerts` response or screenshot.
2. After approval, from `ansible/`, stop only the app01 exporter:

   ```bash
   ansible -i inventory/lab.ini app_servers --become --ask-become-pass --ask-vault-pass \
     -m ansible.builtin.systemd_service -a 'name=prometheus-node-exporter state=stopped'
   ```

3. Observe the app01 node target. With 15-second scrape/evaluation intervals and
   a one-minute pending period, allow scheduling time before expecting a firing
   alert. Record actual timestamps instead of assuming a fixed recovery time.
4. Restore the exporter even if detection fails:

   ```bash
   ansible -i inventory/lab.ini app_servers --become --ask-become-pass --ask-vault-pass \
     -m ansible.builtin.systemd_service -a 'name=prometheus-node-exporter state=started'
   ```

5. Verify the target is up again, inspect alert resolution, and run
   `python3 scripts/check-targets.py` from the repository root with the tunnel open.
6. Save additional redacted outputs and actual screenshots under `docs/screenshots/`,
   then update this record with measured times. Use incident-report.md for details.

The successful reported experiment does not establish container crash recovery,
VM reboot recovery, whole-lab idempotency, high-availability behavior or external
alert delivery. Those are separate tests or unsupported features.
