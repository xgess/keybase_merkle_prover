#!/bin/bash
set -euo pipefail

sudo -i -u keybase bash << EOF
cd /app

set -a; source ./env_file; set +a

nohup bash -c "run_keybase -g 2>&1 | grep -v 'KBFS failed to FUSE mount' &"
sleep 3

python3 /app/run.py
EOF
