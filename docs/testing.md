# Verification results

Generated 22 October 2026, 19:53 IST. Python tests ran against accessledger_test; browser tests use accessledger_test_browser. Original accessledger database is never a test target.

- Python: **85 tests, 0 failures/errors**. Full test names and output: evidence/current/pytest.txt; machine-readable results: pytest.xml.
- Browser: **3 passing tests**. Full output: evidence/current/browser-tests.txt. Tests exercise all five connected operations, six pages, mobile navigation, browser errors and delayed-response request consistency.
- TypeScript and production Vite build: executed successfully; output in evidence/current/frontend-build.txt.
- Database: actual schema/row counts/routines in database-facts.json; all query outputs in sql-output.txt; independent restricted-login ALLOW → revoke → DENY in demonstrations.json.
- Standalone SQL installation was also executed on accessledger_test_sql: eight domain tables, 120 events and the measured index; output: evidence/current/sql-only-install.txt.
- Original evidence SHA-256 and preserved database counts: evidence/current/preservation.json.
- Performance: 100,000 actual evaluated events, five measured plans per query/configuration, captured in benchmark.json and indexing.md.
- Screenshots: six live pages, actual ALLOW/DENY outcomes and mobile view in evidence/current/*.png. These use the live demo; screenshot capture adds real evaluation events.

The Python suite includes 39 retained constraint tests, authorization/default-deny/retention/report tests, eleven two-connection concurrency schedules, and real HTTP integration tests. Fault injection covers audit insertion failure and a deferred failure at COMMIT, proving the API never returns a successful ALLOW for an uncommitted audit event. The database-unavailable response is tested using a real failed connection.

A browser regression first failed while employee/resource/action selectors remained editable during a delayed evaluation response. Disabling selectors while pending fixes misattribution of a returned decision. The independent code review found no critical SQL/API defect; this important UI finding and a legacy evidence-overwrite risk were corrected.

Limitations: Docker Compose is supplied but unexecuted because Docker WSL integration is unavailable. Local PostgreSQL 16.15, Python 3.12 and Node 22 LTS were used instead. Browser tests ran headless Chromium on Linux; other browsers and a formal WCAG audit were not performed. Test output includes a Starlette/httpx deprecation warning and Playwright's NO_COLOR/FORCE_COLOR warning; neither is hidden or counted as a failure. Benchmark timings are local warm-cache observations, not production throughput guarantees. Student identity fields remain for the student to complete. No public deployment or remote push was performed.
