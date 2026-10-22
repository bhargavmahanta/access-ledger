#!/usr/bin/env bash
# Provision a local PostgreSQL 16 cluster without root, Docker, or a system install.
#
# Why this exists: this machine has no reachable PostgreSQL (no server package, no
# Docker WSL integration, sudo needs a password). `apt-get download` runs unprivileged,
# and the .deb payloads are self-contained, so we extract them into a project-local
# prefix and run the real server from there.
#
# Idempotent: re-running reuses .tools/postgres and .pgdata.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="$ROOT/.tools/postgres"
PGDATA="$ROOT/.pgdata"
PGSOCK="$ROOT/.pgsock"
PGPORT="${ACCESSLEDGER_PGPORT:-55432}"
PGUSER="${ACCESSLEDGER_PGUSER:-postgres}"
DEBS="postgresql-16 postgresql-client-16 libpq5"

export LD_LIBRARY_PATH="$PREFIX/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PATH="$PREFIX/usr/lib/postgresql/16/bin:$PATH"

if [ ! -x "$PREFIX/usr/lib/postgresql/16/bin/postgres" ]; then
  echo "==> Fetching PostgreSQL 16 packages (no root required)"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  (cd "$tmp" && apt-get download $DEBS) >/dev/null
  mkdir -p "$PREFIX"
  for d in "$tmp"/*.deb; do dpkg-deb -x "$d" "$PREFIX"; done
  echo "    extracted into .tools/postgres"
fi

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  echo "==> Initialising cluster at .pgdata"
  mkdir -p "$PGDATA" "$PGSOCK"
  chmod 700 "$PGDATA"
  initdb -D "$PGDATA" -U "$PGUSER" -A trust >/dev/null
  # unix socket only: loopback TCP would expose the trust-auth DB to the LAN
  {
    echo "port = $PGPORT"
    echo "unix_socket_directories = '$PGSOCK'"
    echo "listen_addresses = ''"
    echo "log_timezone = 'UTC'"
  } >> "$PGDATA/postgresql.conf"
fi

echo "==> Starting cluster on port $PGPORT"
pg_ctl -D "$PGDATA" -l "$ROOT/.pgdata/server.log" -w start >/dev/null
"$PREFIX/usr/lib/postgresql/16/bin/createdb" -h "$PGSOCK" -p "$PGPORT" -U "$PGUSER" accessledger 2>/dev/null || true

echo "    $(psql -h "$PGSOCK" -p "$PGPORT" -U "$PGUSER" -d accessledger -tAc 'select version()')"
echo "==> Ready. Run: source scripts/db-env.sh"