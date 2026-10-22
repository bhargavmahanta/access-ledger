#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PATH="$ROOT/.tools/node/current/bin:$PATH"
mkdir -p docs/evidence/current
PGDATABASE=accessledger_test scripts/reset-db.sh
PGDATABASE=accessledger_test .venv/bin/python -m pytest -v --junitxml=docs/evidence/current/pytest.xml | tee docs/evidence/current/pytest.txt
npm --prefix frontend run build | tee docs/evidence/current/frontend-build.txt
PGDATABASE=accessledger_test_browser .venv/bin/python scripts/setup-db.py
npm --prefix frontend test | tee docs/evidence/current/browser-tests.txt
.venv/bin/python scripts/verification/capture-evidence.py
.venv/bin/python scripts/verification/benchmark.py
.venv/bin/python scripts/verification/build-report.py
