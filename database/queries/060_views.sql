-- ============================================================================
-- 060 — Views in use
-- Requires database/schema/002_views.sql
-- ============================================================================

\echo '=== 1. vw_active_users_with_roles — active users holding active roles ==='
SELECT department_name, full_name, email, role_name
FROM   vw_active_users_with_roles
ORDER  BY department_name, email, role_name;

\echo ''
\echo '=== 2. vw_effective_user_permissions — FR-04, the core answer ==='
SELECT email, resource_code, action_code
FROM   vw_effective_user_permissions
ORDER  BY email, resource_code, action_code;

\echo ''
\echo '=== 2b. Effective permissions per user, counted ==='
SELECT email, COUNT(*) AS effective_permissions
FROM   vw_effective_user_permissions
GROUP  BY email
ORDER  BY effective_permissions DESC, email;

\echo ''
\echo '=== 2c. Two role paths collapse to one row in the view ==='
\echo '     Viewer and Analyst both grant Priya RES-DB-01:READ; the view returns 1 row.'
SELECT COUNT(*) AS rows_from_view
FROM   vw_effective_user_permissions
WHERE  email = 'priya.sharma@uni.edu'
  AND  resource_code = 'RES-DB-01' AND action_code = 'READ';

\echo ''
\echo '=== 2d. Users with no effective permissions at all ==='
\echo '     Aisha is DISABLED; Chen holds no role. Default-deny, visible as data.'
SELECT u.email, u.status
FROM   app_user u
WHERE  u.email NOT IN (SELECT email FROM vw_effective_user_permissions)
ORDER  BY u.email;

\echo ''
\echo '=== 3. vw_resource_access_summary ==='
SELECT resource_code, resource_type, is_active,
       defined_actions, roles_referencing, users_with_any_role_path,
       attempts, denied
FROM   vw_resource_access_summary
ORDER  BY attempts DESC, resource_code;

\echo ''
\echo '=== 4. vw_access_audit_history — most recent first ==='
SELECT to_char(occurred_at, 'YYYY-MM-DD HH24:MI') AS at,
       rpad(email, 22) AS who,
       rpad(resource_code, 11) AS resource,
       rpad(action_code, 8) AS action,
       rpad(decision, 5) AS result,
       reason_code
FROM   vw_access_audit_history
ORDER  BY occurred_at DESC, log_id DESC
LIMIT  15;

\echo ''
\echo '=== 5. vw_denied_access_attempts — FR-06 denial report ==='
SELECT   email,
         resource_code,
         action_code,
         COUNT(*) AS denied_attempts,
         MIN(occurred_at) AS first_denied,
         MAX(occurred_at) AS last_denied
FROM     vw_denied_access_attempts
GROUP BY email, resource_code, action_code
ORDER BY denied_attempts DESC, email;

\echo ''
\echo '=== 5b. Which user is being repeatedly denied, and why ==='
SELECT   email,
         COUNT(*) AS denials,
         COUNT(DISTINCT reason_code) AS distinct_causes,
         string_agg(DISTINCT reason_code, ', ' ORDER BY reason_code) AS causes
FROM     vw_denied_access_attempts
GROUP BY email
ORDER BY denials DESC, email;