#!/usr/bin/env bash
# Rebuild the database from scratch: schema + synthetic seed.
# Deliberately drops and recreates the database rather than truncating, because
# ACCESS_LOG refuses both UPDATE and DELETE by design.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/db-env.sh"

dropdb --if-exists "$PGDATABASE"
createdb "$PGDATABASE"

psql -q -v ON_ERROR_STOP=1 -f "$ROOT/database/schema/001_core_schema.sql"
psql -q -v ON_ERROR_STOP=1 -f "$ROOT/database/schema/002_views.sql"
psql -q -v ON_ERROR_STOP=1 -f "$ROOT/database/seed/010_seed_demo.sql"

echo "==> Rebuilt '$PGDATABASE'"
psql -c "
    SELECT rpad(relname, 16) AS table, n_live_tup AS rows
    FROM   pg_stat_user_tables ORDER BY relname;"