#!/usr/bin/env bash
# Runs real configuration twice on selected VMs; deployment approval is required.
set -euo pipefail
cd "$(dirname "$0")/../ansible"
first_log="$(mktemp)"
second_log="$(mktemp)"
trap 'rm -f "$first_log" "$second_log"' EXIT
ANSIBLE_NOCOLOR=1 ansible-playbook playbooks/setup.yml "$@" | tee "$first_log"
ANSIBLE_NOCOLOR=1 ansible-playbook playbooks/setup.yml "$@" | tee "$second_log"
python3 - "$first_log" "$second_log" <<'PYTHON'
import re, sys

def recap(path):
    text = open(path).read().rsplit('PLAY RECAP', 1)[-1]
    rows = re.findall(r'^([^\s:]+)\s*:\s*ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)', text, re.M)
    assert rows, 'No host recap found; check inventory and --limit'
    return {host: tuple(map(int, values)) for host, *values in rows}

first, second = map(recap, sys.argv[1:])
assert first.keys() == second.keys(), 'Runs targeted different hosts'
assert all(ok > 0 and changed == unreachable == failed == 0
           for ok, changed, unreachable, failed in second.values()), 'Second run did not converge'
print(f'PASS: second run changed=0 on {", ".join(sorted(second))}')
PYTHON
