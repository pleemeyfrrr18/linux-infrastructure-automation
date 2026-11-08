# Validation and evidence

Review date: **2026-11-08**, Asia/Qyzylorda.

## Operator-confirmed lab results

The project operator confirms these results in the finalization request:

| Result | Evidence available here |
|---|---|
| app01 Docker, Python application and Nginx work | Operator confirmation |
| mon01 Prometheus and Grafana deployed successfully | Operator confirmation |
| Ansible deployment completed on both VMs | Operator confirmation |
| Application smoke test passed | Operator confirmation |
| Stopping/restarting app01 Node Exporter demonstrated alert detection and service recovery | Operator confirmation; see node-exporter-recovery.md |

No deployment transcripts, screenshot images, exact alert payloads, execution
timestamps or measured recovery duration were found in the repository. The
confirmation supports these results without supplying those additional details.
Publication review did not connect to either VM or rerun remote checks.

## Executed local checks during finalization

| Check | Actual result |
|---|---|
| HTTP application suite | **PASS: 6 tests**, real loopback HTTP requests |
| Publication guard regression suite | **PASS: 9 tests**, including a staged secret hidden by a clean working file |
| Public YAML/JSON parsing | **PASS: 31 configuration files** |
| Template/OS checks | **PASS: app/monitoring addresses, noble/resolute Docker sources, supported LTS point releases and Nginx parity** |
| Ansible syntax | **PASS: 5 operational playbooks plus 2 local fixture playbooks** |
| Synthetic preflight | **PASS**, local connection with synthetic Ubuntu 26.04.1 facts |
| Common-role APT fixture | **PASS**, missing file tolerated, multi-stanza source commented, second pass unchanged, unrelated network source preserved |
| Bash syntax | **PASS: all 5 shell scripts** |
| Python dependency consistency | **PASS: pip check reports no broken requirements** |
| Python compilation | **PASS: app, scripts and guard tests** |
| Documentation links | **PASS: local Markdown link targets exist** |
| Publication candidate scan | **PASS: no supported private-key, Vault, token or literal-credential pattern detected** |
| Ignore policy | **PASS: 10 private/local path cases excluded; 3 public examples remain publishable** |

Tooling: Python **3.12.3**, Ansible core **2.20.11**, Jinja **3.1.6**, PyYAML
**6.0.3**, community.docker **5.4.0**, community.general **12.6.7**. Existing
project tooling was used; no system packages were installed.

The HTTP suite needed authorized loopback socket access outside the restricted
sandbox. Local Ansible module fixtures used writable temporary locations via
`ANSIBLE_LOCAL_TEMP` and `ANSIBLE_REMOTE_TEMP`. Neither operation used sudo or
contacted a VM. Temporary fixture creation/cleanup contributes changes to the
fixture play recap; the **second APT repair task itself** reports no change.
This is not a claim of whole-lab zero-change convergence.

The initial fixture attempt discovered that the old CI inventory location could
load the real encrypted group variables. The CI inventory was moved to
`ansible/tests/inventory/`; the final syntax and fixture runs passed without a
Vault password. No secret was decrypted or displayed to fix that problem.

## Publication security review

The branch is `master`, with no commits, no staged files and no configured remote
at review time. There is no prior committed history to audit. The publication
guard scans Git candidates and staged blobs, and reports paths/rules without
printing secret values. Actual local inventory and the existing encrypted Vault
file are ignored, as is `.venv`. These files were not modified.

Private-key/token/password detection is heuristic. A passing scan does not prove
the absence of every possible secret. Manually inspect staged content before
committing or pushing; use docs/publication.md. Screenshots require separate
visual review when added. Currently docs/screenshots contains only its index.

## Not executed during finalization

- Docker Compose config checks, image builds or container integration.
- Promtool configuration validation or synthetic alert-rule tests.
- The GitHub Actions workflow itself; no push was performed.
- Any remote SSH/fact-gathering/service check, package change or deployment.
- Applying the new common-role cdrom.sources repair to either VM.
- Whole-lab idempotency, application process-crash recovery, VM shutdown/reboot,
  clean rebuild, firewall enforcement or historical-data restore tests.

Docker's WSL command reports Docker Desktop integration is unavailable for this
distro. Promtool, ShellCheck and actionlint are not available locally. Bash syntax
and YAML parsing passed; those do not substitute for the missing dedicated tools.
The CI workflow includes the available container/Promtool checks for a future
GitHub run. Its existence is not evidence of a green run.

Use node-exporter-recovery.md for the confirmed experiment, failure-testing.md
for planned tests, incident-report.md for future measured records, and the
screenshots index for actual image evidence. No further VM changes or publication
are authorized by this repository review.
