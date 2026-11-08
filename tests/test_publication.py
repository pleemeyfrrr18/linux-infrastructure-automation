"""Exercise the guard with synthetic credentials; no actual secrets are used."""
import importlib.util
import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('publication', Path(__file__).parents[1] / 'scripts/check-publication.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


class PublicationTests(unittest.TestCase):
    def test_private_key_header(self):
        value = ('-----BEGIN ' + 'OPENSSH PRIVATE KEY-----').encode()
        self.assertIn('private key', publication.findings('accidental.txt', value))

    def test_vault_ciphertext(self):
        value = ('$ANSIBLE_' + 'VAULT;1.1;AES256\n').encode()
        self.assertIn('Ansible Vault ciphertext', publication.findings('accidental.txt', value))

    def test_literal_password(self):
        value = ('grafana_admin_password: ' + 'synthetic-sensitive-value').encode()
        self.assertIn('literal credential assignment', publication.findings('config.yml', value))

    def test_example_placeholder(self):
        self.assertEqual(publication.findings('.env.example', b'GRAFANA_ADMIN_PASSWORD=replace-with-your-own-value'), [])

    def test_reference_is_allowed(self):
        self.assertEqual(publication.findings('role.yml', b'GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:?Set password}'), [])

    def test_private_filename(self):
        self.assertIn('private/local filename', publication.findings('ansible/inventory/lab.ini', b''))
        self.assertIn('private/local filename', publication.findings('config/vault.yml', b''))

    def test_ci_password_is_scoped(self):
        value = b'GRAFANA_ADMIN_PASSWORD=ci-only-password-not-a-real-secret'
        self.assertEqual(publication.findings('scripts/integration.sh', value), [])
        self.assertIn('literal credential assignment', publication.findings('production.env', value))

    def test_staged_secret_cannot_hide_behind_clean_worktree(self):
        with tempfile.TemporaryDirectory(prefix='lia-git-test-') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', directory], check=True)
            value = 'synthetic-' + 'sensitive-value'
            target = root / 'config.yml'
            target.write_text('grafana_admin_password: ' + value)
            subprocess.run(['git', 'add', 'config.yml'], cwd=root, check=True)
            target.write_text('# clean working tree content\n')
            output = io.StringIO()
            with patch.object(publication, 'ROOT', root), contextlib.redirect_stdout(output):
                self.assertEqual(publication.main(), 1)
            self.assertIn('config.yml (index)', output.getvalue())
            self.assertNotIn(value, output.getvalue())

    def test_ignored_local_secret_is_not_a_publication_candidate(self):
        with tempfile.TemporaryDirectory(prefix='lia-git-test-') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', directory], check=True)
            (root / '.gitignore').write_text('local.env\n')
            (root / 'local.env').write_text('grafana_admin_password: ' + 'synthetic-value')
            with patch.object(publication, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(publication.main(), 0)


if __name__ == '__main__':
    unittest.main()
