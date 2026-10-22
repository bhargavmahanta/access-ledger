#!/usr/bin/env bash
# Explicit disposable test/benchmark reset. Never resets either demo or original.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/db-env.sh"
case "$PGDATABASE" in accessledger_test*|accessledger_bench*) ;; *) echo 'Reset requires PGDATABASE=accessledger_test* or accessledger_bench*' >&2; exit 1;; esac
dropdb --if-exists "$PGDATABASE"
"$ROOT/.venv/bin/python" "$ROOT/scripts/setup-db.py"
