# Five connected demonstrations

Start the local application using README.md. Work in accessledger_demo; tests and generated SQL evidence use separate databases. The SQL evidence generator executes the same connected workflow as the browser test and saves actual returned IDs/results in evidence/current/demonstrations.json.

| Demonstration | User action and API | SQL/PL/pgSQL component | Relations and verification |
|---|---|---|---|
| 1. Employee registration | Users → Add employee; POST /api/v1/users | create_user(department_id,full_name,email), FK and email trigger | APP_USER references DEPARTMENT. `SELECT * FROM app_user WHERE email='submission.demo@example.com';` |
| 2. Role assignment | Select employee/role; POST /api/v1/users/{user}/roles/{role} | CALL assign_user_role(user,role), unique pair and activation checks | USER_ROLE, APP_USER, ROLE. `SELECT * FROM user_role WHERE user_id=:user_id;` |
| 3. Permission assignment | Configure role; POST /api/v1/roles/{role}/permissions/{permission} | CALL grant_role_permission(role,permission) | ROLE_PERMISSION, ROLE, PERMISSION; effective lookup joins USER_ROLE and RESOURCE. `SELECT * FROM get_effective_permissions(:user_id);` |
| 4. Access evaluation | Select employee/resource/action; POST /api/v1/evaluations | evaluate_access(user,permission), shared transaction lock, one atomic log insert | APP_USER, USER_ROLE, ROLE, ROLE_PERMISSION, PERMISSION, RESOURCE, ACCESS_LOG. `SELECT * FROM access_log WHERE log_id=:returned_log_id;` |
| 5. Revocation | Revoke role; DELETE /api/v1/users/{user}/roles/{role}, then repeat evaluation | CALL revoke_user_role(user,role), exclusive transaction lock; evaluate_access again | USER_ROLE deletes one current assignment; ACCESS_LOG retains ALLOW and new DENY. `SELECT log_id,decision,reason_code FROM access_log WHERE user_id=:user_id ORDER BY log_id;` |

Use a newly created role as the employee's only provider of the selected permission. If a second active role still grants it, revoking one role correctly leaves ALLOW. Default deny is a policy outcome, not a HTTP failure; valid DENY responses use HTTP 200 and have audit IDs. Unknown references use HTTP 404 and return unlogged DENY with a null ID.

Expected logical outcome is ALLOW → revoke → DENY. Actual timestamps/identifiers and retained joined rows are in demonstrations.json. The API/browser tests verify this result using the real database and restricted application login, rather than mocking decisions.

The cursor report is available through GET /api/v1/reports/activity and directly through `SELECT * FROM generate_access_activity_summary();`. It includes zero-attempt users and total/allowed/denied counts.

Additional manual checks: disable Aisha's user (already disabled in the seed), deactivate a role or resource, remove a role permission, repeat an evaluation, inspect distinct effective permissions and use Audit explorer date/decision filters. Database tests prove these operations and audit-failure rollback; concurrency tests prove both locking schedules.
