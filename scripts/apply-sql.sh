#!/usr/bin/env bash
# Faculty-friendly equivalent of the baseline migration on an EMPTY database.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/db-env.sh"
case "$PGDATABASE" in accessledger_demo|accessledger_test*|accessledger_bench*) ;; *) exit 1;; esac
{ echo 'BEGIN;'; for f in schema/000_roles.sql schema/001_core_schema.sql schema/002_views.sql functions/003_authorization.sql procedures/004_policy.sql functions/005_management.sql cursors/006_activity_summary.sql schema/007_privileges.sql; do cat "$ROOT/database/$f"; echo; done; echo 'COMMIT;'; } | psql -X -v ON_ERROR_STOP=1
