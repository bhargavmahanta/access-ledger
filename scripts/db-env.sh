# Source for the private local cluster. Default never points at historical data.
ACCESSLEDGER_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
export PATH="$ACCESSLEDGER_ROOT/.tools/postgres/usr/lib/postgresql/16/bin:$PATH"
export LD_LIBRARY_PATH="$ACCESSLEDGER_ROOT/.tools/postgres/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PGHOST="${PGHOST:-$ACCESSLEDGER_ROOT/.pgsock}"
export PGPORT="${PGPORT:-${ACCESSLEDGER_PGPORT:-55432}}"
export PGUSER="${PGUSER:-${ACCESSLEDGER_PGUSER:-postgres}}"
export PGDATABASE="${PGDATABASE:-accessledger_demo}"
