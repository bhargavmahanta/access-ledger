# Source this to talk to the project-local cluster:  source scripts/db-env.sh
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
export PATH="$ROOT/.tools/postgres/usr/lib/postgresql/16/bin:$PATH"
export LD_LIBRARY_PATH="$ROOT/.tools/postgres/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PGHOST="$ROOT/.pgsock"
export PGPORT="${ACCESSLEDGER_PGPORT:-55432}"
export PGUSER="${ACCESSLEDGER_PGUSER:-postgres}"
export PGDATABASE=accessledger

# psql invoked with no arguments talks to the project database over the unix socket.
psql() { command psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" "$@"; }