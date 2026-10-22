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
- Frontend GREEN: production TypeScript/Vite build; two browser tests pass including five connected operations and mobile navigation.
- Benchmark: 100,000 genuine evaluated events, five runs per query/config; latest denial median 37.123ms before / 0.035ms after decision/time/log_id index. Full plans captured.
- Independent review: no critical SQL/API defect. Important finding: delayed evaluation response could appear under a changed selector context. Added failing delayed-response browser regression; disable employee/resource/action while pending.
- Review minor fixed: legacy phase1 script now refuses historical regeneration before any output-file write.
- Python final expanded suite GREEN: 85 tests, including NOT NULL rejection across all eight core tables, zero-activity cursor rows, failed COMMIT and actual unavailable-connection handling.
- Browser final GREEN: 3 tests, including delayed real-response selector regression. Live WSL Vite server restarted; polling enabled in WSL to keep file changes visible.
- Fresh evidence captures 10 departments, 20 users, 10 roles, 34 assignments, 12 resources, 33 permissions, 62 grants and 120 evaluated events. All fifteen required queries and supplemental SQL executed.
- Report generated as maintained Markdown plus printable PDF, using actual SQL excerpts, measured benchmark plans and genuine interface screenshots.
- Reviewer follow-up confirms original findings corrected. TCP helpers now use APP_DB_PASSWORD for the restricted login and load .env consistently in Python entry points. Compose itself remains explicitly unexecuted on this host.
- Final reproduction command scripts/verification/run-all.sh exited 0: 85 Python tests, three browser tests, production build, fifteen required SQL queries plus supplemental SQL/cursor, connected scenario and 100k benchmark.
- Final benchmark medians: latest_denials 35.382ms → 0.045ms; full before/after plans in evidence/current/benchmark.json. Earlier ledger measurements describe the earlier run, not the final figures.
- SQL-only installer separately verified on fresh accessledger_test_sql: eight core tables, 120 generated events, decision/time index present.
- Historical evidence confirmed byte-for-byte unchanged (SHA-256 captured), original database retains all eight baseline counts, including 38 events.
- Printable PDF inspected: 14 pages, every page has extractable text; sampled title, query-output and routine pages render correctly.
- Independent review complete; important UI race and minor historical-output risk corrected. No unresolved critical/important findings.
- Remaining external/administrative items: student identity fields must be supplied; Docker Compose execution unavailable on this WSL host. No remote push or public deployment.
