# Troubleshooting

Start with the failing layer and collect evidence before changing configuration.
Commands using sudo or changing service state require your approval.

| Symptom | Inspect | Likely next step |
|---|---|---|
| WSL cannot SSH | `ip route`, VM `ip -br address`, Windows vs WSL reachability | Resolve private routing; a working Windows connection alone is insufficient |
| SSH key refused | `ssh -v INVENTORY_USER@HOST`, remote authorized_keys permissions | Select correct key/agent; do not disable host-key verification |
| Host key changed | Compare fingerprint at console | Remove only the verified obsolete known_hosts entry after confirming a rebuild |
| Ansible sudo failure | Manual SSH and `sudo -v` | Use separate `--limit app01` / `--limit mon01` runs if sudo passwords differ |
| Python/module failure on Ubuntu 26.04 | `ansible --version`, active venv, remote Python | Use project Ansible 2.20; do not downgrade remote Python |
| APT requests a CD-ROM or reports missing installation-media Release file | Inspect `/etc/apt/sources.list.d/cdrom.sources` | See [the common-role repair](apt-installation-media.md); apply only with approval |
| Docker APT 404 or signature conflict | Actual Ubuntu codename and existing Docker source files | Use resolute on 26.04; review duplicate source files before approving edits |
| Vault error | `ansible-vault view` and vault prompt | Supply the right vault password; never print secrets in reports |
| Address preflight fails | `private_ip`, `ip -br address` | Use a real address assigned to the VM, not its NAT gateway |
| Docker unavailable in WSL | `docker version` | Enable Docker Desktop WSL integration; Ansible VM deployment does not require local Docker |
| Port already in use | VM `sudo ss -lntp` | Resolve the conflicting service after approval; host networking needs dedicated ports |
| App fails | On app01, Compose `ps`, `logs app`, `logs nginx` | Inspect Python exceptions, Nginx syntax or bind addresses |
| Proxy returns 502 | app01 `curl http://127.0.0.1:8000/health` | Diagnose application before proxy routing |
| Metrics unavailable | `systemctl status prometheus-node-exporter`, its journal, private port 9100 | Check service bind, firewall source and VM-to-VM route |
| Target down | Prometheus `/targets` → last scrape error | Check actual rendered targets, private addresses and source restrictions |
| Grafana inaccessible | Tunnel output, mon01 `curl http://127.0.0.1:3000/api/health` | Fix tunnel or service; do not expose Grafana publicly |
| Dashboard empty | Data source URL, targets, time range | Wait for rate samples; provisioned data source must use mon01 loopback |
| Grafana password edit has no effect | Existing Grafana volume | Admin environment variables initialize a new DB; rotate through Grafana UI/CLI after approval |
| Changed tasks on second run | Idempotency recap and task output | Check config drift, image replacement and handlers; do not suppress real changes |
| Low disk space | `df -h`, Docker disk usage, Prometheus retention | Review retention/logs; do not prune volumes blindly |

From `/opt/linux-infrastructure-automation/docker` on the appropriate host:

```bash
sudo docker compose -f app.compose.yaml ps
sudo docker compose -f app.compose.yaml logs --tail=100 app nginx
sudo docker compose -f monitoring.compose.yaml ps
sudo docker compose -f monitoring.compose.yaml logs --tail=100 prometheus grafana
sudo journalctl -u prometheus-node-exporter -n 100 --no-pager
```

Run only the Compose file that belongs on that VM. Do not share rendered
`docker compose config` or `docker inspect` output from mon01: environment values
can expose the Grafana password. Use `config --quiet` for validation.
