# Continuous integration

The workflow runs on push, pull request and manual dispatch. It uses read-only
repository permissions, disables persisted checkout credentials, and cancels
superseded runs on the same ref. Bash steps fail on pipeline errors. No CI job
connects to or deploys on the private VMs, and no image is published.

## checks job

Runs on Ubuntu 24.04 with Python 3.12 and the pinned control-node dependencies:

- Publication secret/filename guard, including regression tests.
- Six real local HTTP application tests.
- Public YAML/JSON parsing, private-address/Docker-codename template checks,
  supported Ubuntu point-release checks, documentation links and Bash syntax.
- Syntax checks for deployment and test playbooks.
- Synthetic Ubuntu 26.04.1 preflight assertions with forced local connection.
- The real common-role cdrom.sources task against temporary file fixtures,
  including a second unchanged run and preservation of unrelated sources.

The CI inventory is isolated under `ansible/tests/inventory/`, away from local
inventory/group_vars and encrypted secrets. The fixture's addresses are TEST-NET
values. Local checks do not need your real inventory or Vault password.
Configuration parsing enumerates Git candidates rather than ignored credentials.

## containers job

Runs only after the checks job succeeds, on a separate Ubuntu 24.04 runner:

1. Validate both Compose files without printing environment substitutions.
2. Run Promtool configuration validation and synthetic availability/resource alerts.
3. Build the Python image and start the app/Nginx test stack.
4. Verify proxy health/metrics, non-root app user and read-only container root.
5. Start a monitoring test stack and verify Grafana readiness/dashboard plus
   successful application/Prometheus scrapes. Native host exporters are not
   installed in this container fixture; real-host target checks are separate.

Each integration run creates unique Compose project names. Cleanup removes only
its own containers and named test volumes, leaving deployed projects untouched.
Failure logs are captured before cleanup under ignored `artifacts/integration/`
and uploaded for seven days on CI failure. The only test password is explicitly
public and scoped to disposable integration containers.

## Local checks without VM access

With `.venv` active, from the repository root:

```bash
python -m unittest discover -s app -v
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/check-publication.py
for script in scripts/*.sh; do bash -n "$script"; done
cd ansible
for playbook in playbooks/*.yml tests/*.yml; do
  ansible-playbook -i tests/inventory/ci.ini "$playbook" --syntax-check
done
ansible-playbook -i tests/inventory/ci.ini tests/preflight.yml
ansible-playbook -i tests/inventory/ci.ini tests/apt-sources.yml
```

A restricted environment may need `ANSIBLE_LOCAL_TEMP` and `ANSIBLE_REMOTE_TEMP`
set to writable temporary directories for local fixtures. That is a validation
environment adjustment, not a change to the VMs or production configuration.

A working Linux Docker daemon and free ports 8000/8080/8081/9090/3000 are needed
for the optional container tests. From the repository root:

```bash
GRAFANA_ADMIN_PASSWORD=validation-only-password docker compose -f docker/monitoring.compose.yaml config --quiet
docker compose -f docker/app.compose.yaml config --quiet
scripts/integration.sh
```

Read validation.md for results actually executed. CI definition and successful
static checks do not establish a green GitHub Actions run, correct UFW policy,
VM restart recovery or full Ansible convergence on real hosts.
