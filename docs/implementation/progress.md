# AccessLedger approved implementation ledger

Plan: approved in chat, 2026-10-22. Preserve original database and historical evidence. Eight domain tables, new accessledger_demo database, restricted application login, SQL authoritative, no public deployment.

- Baseline preserved in commit 1ebb24e; implementation branch bhargav/accessledger-completion.
- Tasks: database/setup → routines/concurrency → API → frontend → benchmark/report/evidence → final review.
- Pre-flight: routines return reason/decision/log/timestamp; API commits before return; frontend never computes decisions.
- Ruling: keep existing five reason codes, return invalid-reference reasons outside ACCESS_LOG only.
- Ruling: Alembic version metadata lives in infrastructure schema; exactly eight public domain tables.
- Ruling: UI is local trusted administration, no login/authentication subsystem.
- RED: missing evaluate_access, 206 reported attempts versus 38 actual events, application role accepts forged PERMISSION_GRANTED.
- Ruling: original accessledger_app is cluster-wide; new accessledger_demo_app and accessledger_demo_owner avoid altering its historical privileges.
- Ruling: audit labels are current master-data labels; immutable historical decisions do not imply historical label snapshots.
- Database GREEN: 67 database/concurrency tests pass on accessledger_test. Both lock orders proven for five mutation types; shared evaluation barrier proven.
- Root cause fixed: SQLAlchemy exec_driver_sql passed empty parameters to Psycopg and parsed literal PL/pgSQL percent signs. Baseline execution now uses no_parameters=True.
- Root cause fixed: INSERT SELECT does not guarantee surrogate ID order. Seed lifecycle changes now resolve natural keys; user/permission inserts have explicit ordering.
- API GREEN: six HTTP tests pass, including five connected operations, validation, duplicates, filtering, pagination and invalid-reference behavior.
