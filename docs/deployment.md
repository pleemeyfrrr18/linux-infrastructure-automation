# Deploy the two-VM lab from WSL2

## Existing infrastructure

| Environment | OS | Address | Inventory SSH user |
|---|---|---|---|
| Control node | Ubuntu 24.04 WSL2 | Local | Existing WSL account |
| app01 | Ubuntu Server 26.04.1 LTS | 192.168.56.104 | Read from local inventory |
| mon01 | Ubuntu Server 26.04.1 LTS | 192.168.56.105 | Read from local inventory |

These details were supplied by the operator and read from the working inventory;
The operator reports completed Ansible deployment on both VMs, a passing
application smoke test, and successful Node Exporter alert/recovery testing.
These results are operator-confirmed; publication review did not reconnect to
the VMs. See validation.md for the available evidence.

The working `ansible/inventory/lab.ini` is local and ignored by Git. Preserve it
on an existing lab; do not regenerate SSH keys or replace the known working
configuration. A separate placeholder-only `lab.example.ini` is published.

The required groups are `app_servers` and `monitoring_servers`, one distinct host
each. `private_ip` defaults to the inventory's `ansible_host`; set it explicitly
per host only if the SSH destination differs from the VM's private address.
The architecture always deploys application services to app01 and monitoring
services to mon01. Local CI containers are only tests, not a deployment substitute.

## 1. Prepare compatible control-node tooling

Ubuntu 26.04's default Python is 3.14. Use Ansible core 2.20 on WSL Python 3.12;
older Ubuntu-bundled Ansible is not the supported deployment toolchain.
Do not replace the VMs' Python to accommodate old Ansible.

For a new checkout only, copy `ansible/inventory/lab.example.ini` to `lab.ini`
without overwriting a working inventory, then replace its placeholders.

These commands install only project-local Python tooling and user-local Ansible
collections; run after reviewing them. An assistant must obtain approval before
installing system packages, using sudo or deploying to the VMs.

```bash
# Repository root. If .venv already exists, activate it instead of recreating it.
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-control.txt
ansible-galaxy collection install -r ansible/requirements.yml
ansible --version
```

If Python reports that venv support is missing, approve installation of
`python3-venv` separately. Do not install system packages automatically.
The Ansible/PyYAML versions and direct collections are pinned to the locally
validated baseline. Record OS package versions and image digests with your
deployment evidence; these are not locked by the Python requirements.
WSL Docker is optional for deployment: Ansible builds the app on app01.

Docker is installed from Docker's signed Ubuntu repository, using the target's
actual architecture and `distribution_release` (`resolute` on Ubuntu 26.04),
not a hardcoded `noble` source. Existing conflicting container packages cause
an explicit failure; nothing is automatically uninstalled or pruned.
Node Exporter is installed from Ubuntu's packages, with Python APT bindings.

References: [Docker Ubuntu installation](https://docs.docker.com/engine/install/ubuntu/),
[Ansible Python support matrix](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html),
[Ubuntu 26.04 Python package](https://packages.ubuntu.com/en/resolute/python3).

## 2. Create the Grafana secret

Do not overwrite an existing secret file. From the repository root, generate a
unique password for your own use:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
cd ansible
ansible-vault create inventory/group_vars/all/secrets.yml
```

In the Vault editor enter `grafana_admin_password: YOUR_GENERATED_PASSWORD`.
Use the generated value, not this placeholder. Keep the vault password outside
Git and do not share the generated credential. The application requires at
least 20 characters containing only letters, digits, `_` and `-` so dotenv
substitution is unambiguous. The example file contains no real password.

If the encrypted file already exists, use `ansible-vault edit` instead. A remote
root-owned mode 0600 dotenv supplies Grafana at deployment. Editing this value
after Grafana's database already exists does not automatically rotate the admin
password; use Grafana's supported UI/CLI after approval.

## 3. Run local checks and the non-privileged readiness check

From the repository root, with the venv active:

```bash
python3 -m unittest discover -s app -v
python3 scripts/validate.py
for script in scripts/*.sh; do bash -n "$script"; done
cd ansible
for playbook in playbooks/*.yml; do
  ansible-playbook -i tests/inventory/ci.ini "$playbook" --syntax-check
done
ansible-inventory -i inventory/lab.ini --graph
ansible -i inventory/lab.ini all -m ping --ask-vault-pass
ansible-playbook -i inventory/lab.ini playbooks/preflight.yml --ask-vault-pass
```

The CI inventory contains TEST-NET addresses for syntax checks only. Never deploy
to it. `preflight.yml` gathers facts over SSH without sudo and verifies the OS,
assigned private address, username and two-host topology. It does not install
packages or change SSH/firewall settings. Local syntax checks alone cannot prove
that remote modules work on Ubuntu 26.04.

## 4. Deploy only after explicit approval

The following commands install packages, use sudo on the selected VM, write under
`/opt/linux-infrastructure-automation`, and start services. They do not change
SSH authentication, users, authorized keys or UFW policy. Docker may create
its standard bridge interface and Docker-managed network rules when started;
approval of Docker installation must cover those daemon defaults.
Keep the private network trusted: firewall enforcement remains a separate opt-in.

The hosts have different SSH users; their sudo passwords may also differ. Run
these commands from `ansible/`, app01 first, entering each host's own sudo password:

```bash
ansible-playbook -i inventory/lab.ini playbooks/setup.yml --limit app01 --ask-become-pass --ask-vault-pass
ansible-playbook -i inventory/lab.ini playbooks/setup.yml --limit mon01 --ask-become-pass --ask-vault-pass
```

If both hosts use the same sudo password, a single approved run is also possible:

```bash
ansible-playbook -i inventory/lab.ini playbooks/setup.yml --ask-become-pass --ask-vault-pass
```

For unattended multi-host runs with distinct sudo passwords, store encrypted
`ansible_become_password` variables in host-specific Vault files, never in the
inventory or command line. Do not configure passwordless sudo merely for this lab.

Setup installs host tools, Node Exporter, Docker Engine and Compose, then deploys
and verifies the stack. app01 builds the Python image locally from repository
source. mon01 receives Prometheus scrape targets rendered from inventory,
alert rules, Grafana provisioning and a dashboard. Later application/configuration
updates use `playbooks/deploy.yml` with the same inventory, host limits and
password flags. Run setup first on clean VMs.

## 5. Verify deployed services

From the repository root:

```bash
scripts/smoke-test.sh http://192.168.56.104:8080
scripts/verify-server.sh --ask-vault-pass
```

Verification uses SSH without sudo: it checks the app through Nginx, metrics on
both hosts, Grafana database readiness, the provisioned dashboard and datasource
through Grafana APIs, and four healthy Prometheus targets. The Grafana API tasks
suppress credentials from logs. If a task fails, inspect the matching service
before claiming successful deployment.

For idempotency (these are real deployment runs and require approval):

```bash
scripts/idempotency.sh --limit app01 --ask-become-pass --ask-vault-pass
scripts/idempotency.sh --limit mon01 --ask-become-pass --ask-vault-pass
```

Each script invocation runs setup twice for its selected host and requires zero
changes on the second run. With shared or host-vaulted sudo credentials, omit
`--limit` to check both in one invocation. Cache-refresh changes after an hour
are expected; run the two convergence passes close together.

## 6. Open monitoring with the existing SSH identity

Replace MON_USER and MON_IP with the monitoring host values from your existing
inventory, and select its existing SSH identity/agent. Keep this WSL terminal
running; no remote configuration is changed:

```bash
ssh -N -o ExitOnForwardFailure=yes -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 MON_USER@MON_IP
```

Use `http://localhost:3000`, username `admin`, and your vaulted Grafana password.
The dashboard is under **Dashboards → Lab → Linux Infrastructure Health**.
Prometheus targets: `http://localhost:9090/targets`; alerts: `/alerts`.
From another WSL terminal at the repository root:

```bash
python3 scripts/check-targets.py
```

If Windows-to-WSL localhost forwarding is unavailable, establish an equivalent
tunnel using your existing Windows SSH setup. Do not expose monitoring ports
publicly as a workaround. CPU rate panels need several scrapes to populate.

## 7. Optional firewall — not part of deployment

Do not run the firewall playbook until a separate approval covers its rules.
Review existing UFW rules and the source address seen by SSH on each VM.
Supply actual `admin_cidr` and `lab_cidr` via an operator-created variables file
or extra vars; neither source network is guessed. Keep the VM console open.
The explicit `-e firewall_approved=true` gate is required in addition to approval.
Do not weaken an existing firewall to make deployment pass; investigate and
request approval for any necessary changes.

## VirtualBox rebuild notes

For fresh VMs, use Ubuntu Server 26.04 LTS, approximately 2 vCPU/2 GB RAM/25 GB
disk for app01 and 2 vCPU/3 GB RAM/30 GB disk for mon01. NAT can provide outbound
Internet while a shared host-only adapter provides private addresses. Reserve
addresses, keep the default route on NAT, and verify WSL-to-VM plus VM-to-VM
routing. Do not change the currently working network. Rebuilding hosts requires
new host-key verification and separate approval for any SSH/network changes.
Configuration/dashboard state is reproducible from Git; historical metrics and
Grafana's database need separate backups if valued. Never remove existing VMs
or volumes as part of verification.

## Installation-media APT issue

The common role now disables the dedicated installer `cdrom.sources` file before
its first APT update. This fix is locally regression-tested, not applied to the
already deployed VMs during finalization. See [the detailed explanation](apt-installation-media.md).
