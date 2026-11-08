# Security boundaries and limitations

- No actual credentials or private keys are provided. Inventory and secret files
  are ignored; encrypt real Ansible secrets with Vault. The remote Grafana dotenv
  is root-owned mode 0600. Root/Docker administrators can still inspect container
  environment values. Vault protects repository-at-rest secrets, not remote root.
- Docker runs under root, managed through Ansible sudo. The administrative user
  is not added to the Docker group, which would grant root-equivalent access.
- The application and Nginx run as non-root with read-only roots, dropped
  capabilities, no-new-privileges, bounded resources and bounded Docker logs.
  Prometheus/Grafana retain their image default users and writable data volumes.
- Host networking trades isolation for simpler Linux lab routing. Explicit
  listener bindings matter: private addresses are not public Internet protection
  if your host routes them into an untrusted network.
- Node Exporter is native/systemd. Its package privileges and optional collectors
  follow Ubuntu defaults; review them for stricter environments.
- Prometheus and Grafana bind loopback. Use encrypted SSH tunnels. Nginx serves
  HTTP on a trusted private network, including metrics; TLS is outside this lab's
  baseline. Do not expose it to the public Internet.
- Firewall enforcement is opt-in. Until approved and applied, do not claim the
  lab is firewalled. Existing broad UFW rules are retained and must be reviewed.
  SSH hardening is a documented manual review, not an automatic change.
- Preserve host-key verification and test key login before any future SSH
  restriction. Retain console access. OS security patching is operator-managed.
- Image tags and automation dependencies use a documented baseline. Tags are not
  immutable digests; Docker APT packages and Ubuntu packages are not version
  locked. Review supported releases and vulnerability scans before production.
- No high availability, off-host backups, external uptime monitoring, alert
  delivery, automatic rollback or public deployment is claimed. Prometheus
  cannot alert while its own VM is down.
- Provisioned dashboards/configuration are recoverable from Git. Historical
  metrics and Grafana database state need an independent backup plan if valued.
- The Python standard-library HTTP server is a deliberately small lab workload,
  not a production application platform. GET counters include monitoring traffic.

Reference: Docker explains why published container ports can bypass UFW:
[Docker packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/).
This lab avoids published container ports by using explicitly bound host services.

## Publication review

The working local inventory, encrypted Vault secret file and virtual environment
exist locally and are excluded from publication. No Vault decryption is needed
for safe local CI checks. CI inventory fixtures are kept in a separate directory
so they cannot load local secret group variables. Publication review checks
candidate filenames and supported private-key/token/password patterns without
printing matched values. It is a heuristic, not a comprehensive secret detector;
review staged blobs and screenshots manually before the first push.
