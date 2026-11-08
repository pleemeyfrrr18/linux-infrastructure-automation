# Node Exporter alert and recovery record

Report recorded: **2026-11-08** (Asia/Qyzylorda). The original execution time was
not provided. Evidence source: the operator's confirmation in the project handoff.
No terminal transcript, screenshot or timestamped alert output is currently saved.

## Confirmed report

| Item | Available evidence |
|---|---|
| Baseline | Operator confirms deployed app01 application stack and mon01 monitoring stack |
| Failure action | Node Exporter on app01 was stopped |
| Detection | Operator confirms alert detection was tested successfully |
| Recovery action | Node Exporter on app01 was restarted |
| Recovery result | Operator confirms service recovery was tested successfully |

The exact commands, target response, alert state transitions and recovery duration
were not supplied. The configured alert is `TargetUnavailable` (`up == 0`,
`for: 1m`); that is configuration evidence, not a captured alert payload.
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
6. Save redacted outputs and actual screenshots under `docs/screenshots/`, then
   update this record with measured times. Use incident-report.md for details.

The successful reported experiment does not establish container crash recovery,
VM reboot recovery, whole-lab idempotency, high-availability behavior or external
alert delivery. Those are separate tests or unsupported features.
