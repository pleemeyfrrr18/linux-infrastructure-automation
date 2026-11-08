#!/usr/bin/env python3
"""Check Git publication candidates without displaying secret values.

Heuristic guard, not proof that every possible secret is absent. Ignored local
files are not read. Already tracked files remain candidates even when ignored.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATTERNS = {
    'private key': re.compile(rb'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----'),
    'Ansible Vault ciphertext': re.compile(rb'^\$ANSIBLE_VAULT;', re.M),
    'GitHub token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'AWS access key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'Slack token': re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
}
ASSIGNMENT = re.compile(
    r'^\s*(?:export\s+)?(?:grafana_admin_password|ansible_password|ansible_become_password|'
    r'GRAFANA_ADMIN_PASSWORD|GF_SECURITY_ADMIN_PASSWORD|AWS_SECRET_ACCESS_KEY|'
    r'GITHUB_TOKEN|GH_TOKEN)\s*[:=]\s*(.+?)\s*$', re.M)
PLACEHOLDERS = ('CHANGE_ME', 'YOUR_', 'replace-with-', '{{', '${')
CI_VALUES = {'ci-only-password-not-a-real-secret', 'validation-only-password'}


def findings(name, data):
    """Return rule names only, never matching values."""
    path = Path(name)
    problems = []
    example = '.example' in path.name
    private_names = {'id_rsa', 'id_ed25519', 'id_ecdsa', 'id_dsa', '.vault-password', '.vault_pass'}
    if (path.name in private_names or path.suffix.lower() in {'.key', '.pem', '.p12', '.pfx'}
            or '.ssh' in path.parts or '.venv' in path.parts or 'venv' in path.parts
            or (path.name.startswith('.env') and path.name != '.env.example')
            or name == 'ansible/inventory/lab.ini'
            or (not example and re.match(r'^(?:secrets|vault|credentials)(?:[._-]|$)', path.name))):
        problems.append('private/local filename')
    for rule, pattern in TOKEN_PATTERNS.items():
        if pattern.search(data):
            problems.append(rule)
    text = data.decode('utf-8', errors='replace')
    for match in ASSIGNMENT.finditer(text):
        value = match.group(1).strip(' \t\'"')
        if not value or value.startswith(PLACEHOLDERS):
            continue
        if value.split()[0] in CI_VALUES and (name.startswith(('scripts/', '.github/', 'docs/')) or example):
            continue
        problems.append('literal credential assignment')
    return sorted(set(problems))


def main():
    result = subprocess.run(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        cwd=ROOT, check=True, stdout=subprocess.PIPE)
    names = sorted(set(n.decode('utf-8') for n in result.stdout.split(b'\0') if n))
    failures = []
    for name in names:
        path = ROOT / name
        if path.is_symlink():
            failures.append((name, ['symlink requires manual publication review']))
        elif path.is_file():
            problems = findings(name, path.read_bytes())
            if problems:
                failures.append((name, problems))
    # Inspect staged blobs too: a clean working file must not hide an older
    # credential that remains in the index awaiting publication.
    index = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT)
    for entry in index.split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, object_id, _stage = metadata.split()
        name = raw_name.decode('utf-8')
        if mode not in (b'100644', b'100755'):
            failures.append((name + ' (index)', ['non-regular staged entry requires review']))
            continue
        data = subprocess.check_output(['git', 'cat-file', 'blob', object_id.decode()], cwd=ROOT)
        problems = findings(name, data)
        if problems:
            failures.append((name + ' (index)', problems))
    for name, problems in failures:
        print(f'FAIL: {name}: {", ".join(problems)}')
    if failures:
        return 1
    print(f'PASS: scanned {len(names)} Git publication candidates; no supported secret patterns detected')
    print('Review staged content manually; this heuristic does not detect every possible credential.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
