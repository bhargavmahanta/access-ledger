-- ============================================================================
-- 030 — Joins: INNER, LEFT, multi-table, self-join
-- ============================================================================

\echo '=== 1. INNER JOIN — users who hold roles, with their department and role ==='
SELECT u.email, d.department_name, r.role_name
FROM       app_user  u
JOIN       department d ON d.department_id = u.department_id
JOIN       user_role ur ON ur.user_id      = u.user_id
JOIN       role      r  ON r.role_id       = ur.role_id
ORDER BY   u.email, r.role_name;

\echo ''
\echo '=== 2. LEFT JOIN — every user, including Chen Wei who has no roles ==='
SELECT u.email, u.status, r.role_name
FROM       app_user  u
LEFT JOIN user_role ur ON ur.user_id = u.user_id
LEFT JOIN role      r  ON r.role_id  = ur.role_id
ORDER BY   (r.role_name IS NOT NULL), u.email;

\echo ''
\echo '=== 3. Multi-table join (5 tables) — FR-04: effective permissions ==='
\echo '    A permission counts only when the user, the role and the resource are active.'
SELECT DISTINCT
       u.email, s.resource_code, s.type, p.action_code
FROM       app_user         u
JOIN       user_role        ur ON ur.user_id      = u.user_id
JOIN       role             r  ON r.role_id       = ur.role_id
JOIN       role_permission  rp ON rp.role_id      = r.role_id
JOIN       permission       p  ON p.permission_id = rp.permission_id
JOIN       resource         s  ON s.resource_id   = p.resource_id
WHERE      u.status = 'ACTIVE'
  AND      r.is_active
  AND      s.is_active
ORDER BY   u.email, s.resource_code, p.action_code;

\echo ''
\echo '=== 3b. UNION semantics made visible: 2 role paths, 1 effective permission ==='
\echo '     Priya reaches RES-DB-01:READ through both Viewer and Analyst, but holds'
\echo '     it once. Without DISTINCT this query would report her access twice.'
SELECT   u.email, s.resource_code, p.action_code,
         COUNT(*)        AS role_paths,
         COUNT(DISTINCT r.role_id) AS distinct_roles,
         string_agg(r.role_name, ', ' ORDER BY r.role_name) AS granted_via
FROM       app_user         u
JOIN       user_role        ur ON ur.user_id      = u.user_id
JOIN       role             r  ON r.role_id       = ur.role_id
JOIN       role_permission  rp ON rp.role_id      = r.role_id
JOIN       permission       p  ON p.permission_id = rp.permission_id
JOIN       resource         s  ON s.resource_id   = p.resource_id
WHERE      u.email = 'priya.sharma@uni.edu'
  AND      s.resource_code = 'RES-DB-01'
  AND      p.action_code = 'READ'
  AND      u.status = 'ACTIVE' AND r.is_active AND s.is_active
GROUP BY  u.email, s.resource_code, p.action_code;

\echo ''
\echo '=== 3c. The same permission, as the effective-permissions view reports it ==='
SELECT email, resource_code, action_code
FROM   vw_effective_user_permissions
WHERE  email = 'priya.sharma@uni.edu'
  AND  resource_code = 'RES-DB-01' AND action_code = 'READ';

\echo ''
\echo '=== 4. SELF JOIN — who shares a department with someone holding Administrator? ==='
SELECT a.full_name AS staff_member,
       a.email,
       d.department_name,
       b.full_name AS holds_administrator,
       b.email     AS admin_email
FROM       app_user a
JOIN       app_user b ON b.user_id <> a.user_id
                 AND b.department_id = a.department_id
JOIN       user_role ur ON ur.user_id = b.user_id
JOIN       role      r  ON r.role_id  = ur.role_id
JOIN       department d ON d.department_id = a.department_id
WHERE      r.role_name = 'Administrator'
ORDER BY   d.department_name, a.full_name;

\echo ''
\echo '=== 5. LEFT JOIN + anti-join: users with no roles at all ==='
SELECT u.email, u.full_name
FROM       app_user u
LEFT JOIN  user_role ur ON ur.user_id = u.user_id
WHERE      ur.user_id IS NULL;

\echo ''
\echo '=== 6. LEFT JOIN on the audit side — permissions never attempted ==='
SELECT p.permission_id, s.resource_code, p.action_code, COUNT(l.log_id) AS attempts
FROM       permission p
JOIN       resource  s ON s.resource_id = p.resource_id
LEFT JOIN  access_log l ON l.permission_id = p.permission_id
GROUP BY   p.permission_id, s.resource_code, p.action_code
ORDER BY   attempts, s.resource_code, p.action_code;