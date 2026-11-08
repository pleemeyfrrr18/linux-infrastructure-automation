#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../ansible"
exec ansible-playbook playbooks/verify.yml "$@"
