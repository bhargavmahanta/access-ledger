-- ============================================================================
-- 050 — Subqueries: scalar, IN, EXISTS, correlated
-- ============================================================================

\echo '=== 1. SCALAR subquery — each user''s denial count beside their name ==='
SELECT   u.email,
         (SELECT COUNT(*) FROM access_log l
           WHERE l.user_id = u.user_id AND l.decision = 'DENY') AS denials
FROM       app_user u
ORDER BY   denials DESC, u.email;

\echo ''
\echo '=== 2. Scalar subquery in FROM — a derived table: users with no roles ==='
SELECT u.user_id, u.full_name, u.email
FROM       app_user u
WHERE      NOT EXISTS (SELECT 1 FROM user_role ur WHERE ur.user_id = u.user_id)
ORDER BY   u.user_id;

\echo ''
\echo '=== 3. IN — active users who have attempted something DENIED ==='
SELECT u.user_id, u.full_name, u.email
FROM   app_user u
WHERE  u.status = 'ACTIVE'
  AND  u.user_id IN (SELECT l.user_id FROM access_log l WHERE l.decision = 'DENY')
ORDER  BY u.user_id;

\echo ''
\echo '=== 4. NOT IN — resources that were never the subject of an ALLOWED attempt ==='
\echo '     (NULL-safe check: NOT IN is unsafe when the subquery can yield NULL)'
SELECT r.resource_id, r.resource_code, r.name
FROM   resource r
WHERE  r.resource_id NOT IN (
           SELECT p.resource_id FROM access_log l
           JOIN   permission p ON p.permission_id = l.permission_id
           WHERE  l.decision = 'ALLOW')
ORDER  BY r.resource_id;

\echo ''
\echo '=== 5. EXISTS (semi-join) — permissions granted by more than one role ==='
SELECT p.permission_id, s.resource_code, p.action_code
FROM   permission p
JOIN   resource  s ON s.resource_id = p.resource_id
WHERE  EXISTS (SELECT 1 FROM role_permission a
                WHERE a.permission_id = p.permission_id)
  AND  EXISTS (SELECT 1 FROM role_permission b
                WHERE b.permission_id = p.permission_id
                  AND b.role_id <> (SELECT min(role_id) FROM role_permission c
                                      WHERE c.permission_id = p.permission_id))
ORDER  BY s.resource_code, p.action_code;

\echo ''
\echo '=== 6. CORRELATED subquery in a WHERE clause — users with NO audit history ==='
SELECT u.user_id, u.full_name, u.email, u.status
FROM   app_user u
WHERE  NOT EXISTS (
           SELECT 1 FROM access_log l
           WHERE l.user_id = u.user_id)
ORDER  BY u.user_id;

\echo ''
\echo '=== 7. CORRELATED subquery — "more than the average" attempts per user ==='
SELECT u.email, COUNT(l.log_id) AS attempts
FROM   app_user u
JOIN   access_log l ON l.user_id = u.user_id
GROUP  BY u.user_id, u.email
HAVING COUNT(l.log_id) > (SELECT AVG(cnt) FROM (
                             SELECT COUNT(*) AS cnt FROM access_log
                             GROUP BY user_id) AS per_user)
ORDER  BY attempts DESC, u.email;

\echo ''
\echo '=== 8. Nested correlated subquery — has this user ever been denied ==='
SELECT u.email, u.status,
       CASE WHEN EXISTS (SELECT 1 FROM access_log l
                          WHERE l.user_id = u.user_id AND l.decision = 'DENY')
            THEN 'has denials on record' ELSE 'clean record' END AS standing
FROM   app_user u
ORDER  BY standing, u.email;