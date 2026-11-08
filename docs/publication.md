# Manual GitHub publication

Current review baseline: the repository has **no commits**, the branch is
`master`, there are no staged files, and no Git remote is configured.
Publication is not performed by the assistant. These instructions publish only
after your own staged review and approval.

## Safety review

The existing local inventory and encrypted Ansible Vault secret file are ignored.
The virtual environment is also ignored. Private keys, dotenv credentials,
Vault/password files and local logs are excluded. Publication candidates are
scanned for supported credential patterns without printing matching values.
There is no committed history to audit at this baseline.

Activate the venv and run from the repository root:

```bash
python scripts/check-publication.py
git status --short
git check-ignore .venv/ ansible/inventory/lab.ini ansible/inventory/group_vars/all/secrets.yml
```

A passing heuristic scan is not a guarantee that every possible secret is absent.
Examples contain placeholders and ephemeral CI-only credentials, not real lab
passwords. Manually review staged files, new images and any saved logs. Do not
force-add ignored files. This project keeps encrypted Vault ciphertext out of
Git too, even though encrypted files can be safely versioned under other policies.

## First commit and push

Create an **empty** GitHub repository called `linux-infrastructure-automation`
without adding a remote README/license/gitignore. Substitute your real GitHub
username in the SSH remote URL. Configure Git identity if Git prompts for it;
do not copy an invented name or email.

```bash
git add .
python scripts/check-publication.py
git diff --cached --check
git diff --cached --stat
git diff --cached --name-only
git diff --cached
```

Stop and review that output locally before proceeding. It must not include
`.venv`, `lab.ini`, secret/Vault/password files, private keys or unrelated logs.
Then:

```bash
git commit -m "Finalize two-VM Linux infrastructure automation portfolio"
git branch -M main
git remote add origin git@github.com:YOUR_GITHUB_USERNAME/linux-infrastructure-automation.git
git remote -v
git push -u origin main
```

If a remote has been configured since this review, inspect it instead of adding
or replacing it blindly. A push triggers CI. Check both CI jobs on GitHub and
record their actual result; the workflow has not been run by publication review.
If a genuine secret is ever committed or exposed, revoke/rotate it before
following a deliberate history-cleanup plan; deleting the working file alone
does not remove committed copies.
