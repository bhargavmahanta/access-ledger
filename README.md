# AccessLedger

**A relational database for access control and audit records.**

Database Systems project — BCSE302L / BCSE302P. The database is the deliverable;
the schema, the SQL and the constraint tests are the product.

AccessLedger models who a user is, which roles they hold, which actions those
roles permit on registered resources, and the outcome of every recorded access
attempt.

---

## Status — Review 2, Phase 1

| Area | State |
|---|---|
| Relational schema (8 relations) | **Complete** — implemented and running |
| Normalization analysis | **Complete** — 3NF proven, BCNF assessed |
| ER diagram | **Complete** — Crow's Foot, Mermaid |
| Synthetic seed data | **Complete** — deterministic, 8 users / 38 events |
| SQL demonstrations | **Complete** — joins, aggregation, subqueries, views |
| Integrity tests | **Complete** — 39 passing against a real database |
| Access-evaluation routine | Not started — Phase 2 |
| Transactions & concurrency | Not started — Phase 3 |
| Indexing & `EXPLAIN ANALYZE` | Not started — Phase 3 |
| Backend / frontend | Not started — later phases |

Executed results, not claims: **[`docs/evidence/phase1-run.md`](docs/evidence/phase1-run.md)**.

---

## Quick start

No Docker, no root, no system install required.

```bash
./scripts/bootstrap-postgres.sh     # fetch + start a private PostgreSQL 16
./scripts/reset-db.sh               # build schema, views, seed data
source scripts/db-env.sh            # psql/createdb now target this database
psql                               # interactive shell
```

Run the SQL demonstrations and the tests:

```bash
for f in database/queries/*.sql; do psql -f "$f"; done
.venv/bin/pytest tests/database -v
```

Regenerate the evidence file from a fresh run:

```bash
./scripts/run-phase1-evidence.sh
```

### Why the bootstrap script exists

This machine had no reachable PostgreSQL — no server package, Docker WSL
integration disabled, and `sudo` requiring a password. `apt-get download` runs
unprivileged and the Debian payloads are self-contained, so the script extracts
PostgreSQL 16.15 into `.tools/postgres/` and runs the real server from there. It
listens on a unix socket only (`listen_addresses = ''`), so the trust-authenticated
cluster is never reachable off the machine.

This is also the reproducible-setup artifact Review 3 asks for: delete
`.tools/` and `.pgdata/`, re-run the script, and the database is rebuilt from
nothing.

---

## Layout

```
docs/
  database-design.md      the eight relations, and every design decision
  normalization.md        functional dependencies, 1NF → 3NF → BCNF
  er-diagram.md           Crow's Foot ER diagram (Mermaid)
  evidence/phase1-run.md  captured output of an actual run
database/
  schema/001_core_schema.sql   tables, keys, checks, integrity triggers
  schema/002_views.sql         the five reporting views
  seed/010_seed_demo.sql       synthetic demonstration data
  queries/020..060             basic SQL, joins, aggregation, subqueries, views
tests/database/                39 integrity tests against a real database
scripts/                       bootstrap, env, reset, evidence capture
```

`database/schema/*.sql` is the **authoritative** definition of the schema. When
the backend arrives, SQLAlchemy models will be verified against it rather than
defining it — two sources of truth for one schema is how they drift apart.

---

## The model

Eight relations, two of them junctions:

```
DEPARTMENT 1─* APP_USER
APP_USER   1─* USER_ROLE      *─1 ROLE          ← user ↔ role
ROLE       1─* ROLE_PERMISSION *─1 PERMISSION  ← role ↔ permission
RESOURCE   1─* PERMISSION
APP_USER   1─* ACCESS_LOG     *─1 PERMISSION
```

A permission is one action on one resource, uniquely identified by
`(resource_id, action_code)`. `ACCESS_LOG` reaches its resource through
`PERMISSION` rather than storing `resource_id` a second time.

An attempt is **allowed** only when the user is active, the resource is active,
and at least one active role assigned to that user carries the permission.
Otherwise it is **denied** — default deny.

---

## Two decisions worth knowing about

**`access_log.decision` is generated, not supplied.** `reason_code` is the
controlled vocabulary, and `ALLOW` is exactly what `PERMISSION_GRANTED` means, so
PostgreSQL computes one from the other:

```sql
decision VARCHAR(5) GENERATED ALWAYS AS
    (CASE WHEN reason_code = 'PERMISSION_GRANTED' THEN 'ALLOW' ELSE 'DENY' END) STORED
```

Impossible pairs such as `ALLOW` + `USER_DISABLED` cannot be stored, and the
caller cannot pick the outcome. The cost is a strict BCNF violation
(`reason_code → decision`, and `reason_code` is not a superkey) that is inherited
from the specified design and is analysed in
[`docs/normalization.md`](docs/normalization.md) §6.

**Audit events are append-only, in two layers.** A trigger refuses `UPDATE`,
`DELETE` and `TRUNCATE` on `access_log` — including for the table owner, whom
privileges do not constrain — and the `accessledger_app` role is granted only
`SELECT, INSERT` on it. This stops ordinary and privileged mistakes; it does not
stop a superuser who drops the trigger. [`docs/database-design.md`](docs/database-design.md) §4.6
records that limit rather than overclaiming.

---

## Deliberately not built

Role inheritance, direct user→permission grants, explicit deny rules, access
request/approval workflows, multi-tenancy, SSO — each excluded by the Review 1
scope. Each would add a ninth entity or duplicate an existing fact. Adding one
later means a schema change, which is why they are listed rather than left
available.