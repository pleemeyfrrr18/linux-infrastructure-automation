#!/usr/bin/env python3
"""Parse repository YAML and JSON; Jinja templates are checked separately."""
import json
from pathlib import Path
import yaml
import subprocess
root = Path(__file__).resolve().parents[1]
count = 0
candidates = subprocess.check_output(
    ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root
).split(b'\0')
for name in sorted(set(candidates)):
    if not name:
        continue
    path = root / name.decode()
    if not path.is_file() or path.relative_to(root).parts[0] not in ('ansible', 'docker', 'monitoring', '.github'):
        continue
    if path.suffix in ('.yaml', '.yml'):
        list(yaml.safe_load_all(path.read_text()))
        count += 1
    elif path.suffix == '.json':
        json.loads(path.read_text())
        count += 1
print(f"PASS: parsed {count} YAML/JSON files")

from jinja2 import Environment, StrictUndefined
import re

env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
# TEST-NET addresses are fixtures only, never deployment defaults.
fixture = {
    "private_ip": "192.0.2.20",
    "groups": {"app_servers": ["app01"]},
    "hostvars": {"app01": {"private_ip": "192.0.2.10"}},
}
template = root / "ansible/roles/monitoring/templates/prometheus.yml.j2"
config = yaml.safe_load(env.from_string(template.read_text()).render(**fixture))
assert config["scrape_configs"][0]["static_configs"][0]["targets"] == ["192.0.2.10:9100"]
assert config["scrape_configs"][0]["static_configs"][1]["targets"] == ["192.0.2.20:9100"]
assert config["scrape_configs"][1]["static_configs"][0]["targets"] == ["192.0.2.10:8080"]
template = root / "ansible/roles/application/templates/nginx.conf.j2"
assert env.from_string(template.read_text()).render(private_ip="127.0.0.1") == (
    root / "docker/nginx/nginx.conf"
).read_text()
for path in [root / "README.md", *(root / "docs").glob("*.md")]:
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
        if not target.startswith(("http:", "https:", "#")):
            assert (path.parent / target.split("#")[0]).exists(), (path, target)
print("PASS: rendered address fixtures, Nginx template parity and documentation links")

# Ensure Docker's repository follows the target OS, including 26.04 point releases.
docker_tasks = yaml.safe_load((root / "ansible/roles/docker/tasks/main.yml").read_text())
repo_task = next(t for t in docker_tasks if "ansible.builtin.copy" in t)
for codename in ("noble", "resolute"):
    source = env.from_string(repo_task["ansible.builtin.copy"]["content"]).render(
        ansible_facts={"architecture": "x86_64", "distribution_release": codename})
    assert f"ubuntu {codename} stable" in source
    assert "arch=amd64" in source
print("PASS: Docker repository rendering for noble and resolute")

# Check the actual preflight expression against LTS point-release facts.
env.tests['match'] = lambda value, pattern: re.match(pattern, value) is not None
preflight = yaml.safe_load((root / 'ansible/roles/preflight/tasks/main.yml').read_text())
version_check = next(
    expression
    for task in preflight
    for expression in task.get('ansible.builtin.assert', {}).get('that', [])
    if 'distribution_version is match' in expression
)
check_version = env.compile_expression(version_check)
for version in ('24.04', '24.04.3', '26.04', '26.04.1'):
    assert check_version(ansible_facts={'distribution_version': version}), version
for version in ('22.04', '25.10', '26.10'):
    assert not check_version(ansible_facts={'distribution_version': version}), version
print('PASS: preflight accepts supported LTS point releases and rejects unsupported releases')
