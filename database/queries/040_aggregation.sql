-- ============================================================================
-- 040 — Aggregation: COUNT, GROUP BY, HAVING, multi-level aggregates
-- ============================================================================

\echo '=== 1. COUNT and GROUP BY — attempts per user, split by outcome ==='
SELECT   u.email,
         COUNT(l.log_id)                                        AS total,
         COUNT(*) FILTER (WHERE l.decision = 'ALLOW')            AS allowed,
         COUNT(*) FILTER (WHERE l.decision = 'DENY')             AS denied,
         MIN(l.occurred_at)                                     AS first_attempt,
         MAX(l.occurred_at)                                     AS last_attempt
FROM       app_user  u
JOIN       access_log l ON l.user_id = u.user_id
GROUP BY   u.email
ORDER BY   total DESC, u.email;

\echo ''
\echo '=== 2. HAVING — only users with a denial rate above one quarter ==='
SELECT   u.email,
           COUNT(l.log_id) AS total,
           COUNT(*) FILTER (WHERE l.decision = 'DENY') AS denied,
           round(100.0 * COUNT(*) FILTER (WHERE l.decision = 'DENY')
                 / COUNT(l.log_id), 1) AS denial_rate_pct
FROM       app_user  u
JOIN       access_log l ON l.user_id = u.user_id
GROUP BY   u.email
HAVING     COUNT(*) FILTER (WHERE l.decision = 'DENY') * 4 > COUNT(l.log_id)
ORDER BY   denial_rate_pct DESC, u.email;

\echo ''
\echo '=== 3. GROUP BY on a derived column — denial reasons, grouped ==='
SELECT   reason_code,
         decision,
         COUNT(*) AS events,
         min(occurred_at) AS first_seen,
         max(occurred_at) AS last_seen
FROM       access_log
GROUP BY   reason_code, decision
ORDER BY   events DESC, reason_code;

\echo ''
\echo '=== 4. Multi-level aggregation — per resource, then per resource and action ==='
SELECT   s.resource_code,
         s.type,
         COUNT(l.log_id)                                       AS attempts,
         COUNT(*) FILTER (WHERE l.decision = 'DENY')            AS denied,
         COUNT(DISTINCT l.user_id)                             AS distinct_users,
         ROUND(AVG(COUNT(l.log_id)) OVER (PARTITION BY s.type), 2) AS avg_attempts_for_type
FROM       resource   s
JOIN       permission p ON p.resource_id = s.resource_id
JOIN       access_log l ON l.permission_id = p.permission_id
GROUP BY   s.resource_code, s.type
ORDER BY   attempts DESC, s.resource_code;

\echo ''
\echo '=== 5. Role usage — how many assignments each role carries ==='
SELECT   r.role_name,
         r.is_active,
         COUNT(DISTINCT ur.user_id)     AS assigned_users,
         COUNT(DISTINCT rp.permission_id) AS permissions_granted,
         COUNT(*) FILTER (WHERE NOT r.is_active) AS inactive_flag
FROM       role             r
LEFT JOIN  user_role        ur ON ur.role_id = r.role_id
LEFT JOIN  role_permission  rp ON rp.role_id = r.role_id
GROUP BY   r.role_id, r.role_name, r.is_active
ORDER BY   assigned_users DESC, r.role_name;

\echo ''
\echo '=== 6. Monthly volume — a time series via date_trunc ==='
SELECT   to_char(date_trunc('month', l.occurred_at), 'YYYY-MM') AS month,
         COUNT(*)                                              AS attempts,
         COUNT(*) FILTER (WHERE l.decision = 'ALLOW')          AS allowed,
         COUNT(*) FILTER (WHERE l.decision = 'DENY')           AS denied
FROM       access_log l
GROUP BY   1
ORDER BY   1;

\echo ''
\echo '=== 7. HAVING over a JOIN with no matching rows (LEFT JOIN + IS NULL) ==='
SELECT   s.resource_code, s.type, COUNT(p.permission_id) AS action_count
FROM       resource   s
LEFT JOIN  permission p ON p.resource_id = s.resource_id
GROUP BY   s.resource_code, s.type
HAVING     COUNT(p.permission_id) >= 3
ORDER BY   action_count DESC, s.resource_code;