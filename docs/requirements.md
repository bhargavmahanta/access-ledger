# Requirements and evidence map

Authority: user-pasted master implementation prompt and approved implementation plan. The four referenced PDFs are unavailable; this project does not invent extra faculty criteria. BCSE302L / BCSE302P, VIT Vellore. Review 1: concept/design; Review 2: relational SQL; Review 3: routines, integration and verification.

| Requirement | Implementation | Executed evidence |
|---|---|---|
| Exactly eight related domain tables | database/schema/001_core_schema.sql | current/sql-output.txt; current/sql-only-install.txt; schema tests |
| PK, FK, NOT NULL, UNIQUE, CHECK, DEFAULT | Core DDL, normalization trigger | pytest constraint tests |
| At least ten records per table | database/seed/020_complete_demo.sql | current/sql-output.txt |
| Crow's Foot ER + relational schema + FDs | er-diagram.md; relational-schema.md; normalization.md; er-diagram.svg | Diagram derived from live schema |
| At least fifteen SQL queries | database/queries/010_required_catalog.sql | current/sql-output.txt |
| INSERT, UPDATE, DELETE | Department lifecycle; assignment/grant/revocation routines | current/sql-output.txt; current/demonstrations.json |
| Two stored procedures | assign_user_role, revoke_user_role, additional controlled procedures | current/sql-output.txt; pytest |
| Two stored functions | evaluate_access, get_effective_permissions | current/sql-output.txt; pytest |
| Explicit meaningful cursor | generate_access_activity_summary | current/sql-output.txt; pytest |
| Two meaningful triggers | Append-only audit; frozen permission identity | pytest owner and actual-login tests |
| Default deny and transactional audit | evaluate_access + API explicit commit | pytest authorization/failure tests |
| Concurrent revocation and evaluations | Shared/exclusive transaction advisory lock | Eleven two-connection tests in pytest |
| Views and reports | Six vw_* views, report endpoints | current/sql-output.txt; API tests |
| Indexes / EXPLAIN ANALYZE | Baseline indexes + measured decision/time index | indexing.md; current/benchmark.json |
| Python database connectivity and API | FastAPI + SQLAlchemy + Psycopg | API integration tests |
| Five integrated operations | Browser workflow + API + SQL scenario | current/browser-tests.txt; current/demonstrations.json |
| Six real connected frontend pages | frontend/src/pages | Browser tests; current/*.png |
| Report / real outputs / reproduction | final-report.md and PDF; README | Generated evidence files |

Paths beginning current/ are relative to docs/evidence/. Inspect testing.md for the actual final results and limitations; a source file alone is not execution evidence.
