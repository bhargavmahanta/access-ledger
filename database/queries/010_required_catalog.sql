-- Exact faculty catalog. Override values with psql -v user_id=... etc.
\if :{?user_id}
\else
\set user_id 1
\endif
\if :{?department_id}
\else
\set department_id 1
\endif
\if :{?permission_id}
\else
\set permission_id 1
\endif
\echo 'Q01 Active employees'
SELECT user_id,full_name,email FROM app_user WHERE status='ACTIVE' ORDER BY user_id;
\echo 'Q02 Employees by department'
SELECT d.department_name,u.full_name,u.email FROM department d JOIN app_user u USING(department_id) WHERE d.department_id=:department_id ORDER BY u.user_id;
\echo 'Q03 Users and assigned roles, including users with no roles'
SELECT u.full_name,r.role_name FROM app_user u LEFT JOIN user_role ur USING(user_id) LEFT JOIN role r USING(role_id) ORDER BY u.user_id,r.role_id;
\echo 'Q04 Active assigned roles for selected user'
SELECT r.role_id,r.role_name FROM user_role ur JOIN role r USING(role_id) WHERE ur.user_id=:user_id AND r.is_active ORDER BY r.role_id;
\echo 'Q05 Resource-specific role permissions'
SELECT r.role_name,s.resource_code,p.action_code FROM role r JOIN role_permission rp USING(role_id) JOIN permission p USING(permission_id) JOIN resource s USING(resource_id) ORDER BY r.role_id,p.permission_id;
\echo 'Q06 Distinct effective permissions'
SELECT DISTINCT * FROM get_effective_permissions(:user_id);
\echo 'Q07 Users per role, including empty roles'
SELECT r.role_name,count(ur.user_id) AS users FROM role r LEFT JOIN user_role ur USING(role_id) GROUP BY r.role_id ORDER BY r.role_id;
\echo 'Q08 Roles held by more than two users'
SELECT r.role_name,count(*) AS users FROM role r JOIN user_role ur USING(role_id) GROUP BY r.role_id HAVING count(*)>2 ORDER BY users DESC,r.role_id;
\echo 'Q09 Users without assigned roles (subquery)'
SELECT u.user_id,u.full_name FROM app_user u WHERE NOT EXISTS(SELECT 1 FROM user_role ur WHERE ur.user_id=u.user_id) ORDER BY u.user_id;
\echo 'Q10 Denied access attempts'
SELECT * FROM vw_denied_access_attempts ORDER BY occurred_at DESC,log_id DESC;
\echo 'Q11 Denied attempts per user'
SELECT * FROM vw_denied_access_summary ORDER BY denied_attempts DESC,user_id;
\echo 'Q12 Most frequently accessed resources'
SELECT resource_code,attempts,denied FROM vw_resource_access_summary ORDER BY attempts DESC,resource_id;
\echo 'Q13 Audit history in a selected interval: last seven days'
SELECT * FROM vw_access_audit_history WHERE occurred_at>=CURRENT_TIMESTAMP-INTERVAL '7 days' AND occurred_at<CURRENT_TIMESTAMP ORDER BY occurred_at,log_id;
\echo 'Q14 Users possessing selected permission'
SELECT user_id,full_name,email FROM vw_effective_user_permissions WHERE permission_id=:permission_id ORDER BY user_id;
\echo 'Q15 Complete joined audit report'
SELECT l.log_id,u.full_name,d.department_name,r.resource_code,p.action_code,l.decision,l.reason_code,l.occurred_at FROM access_log l JOIN app_user u USING(user_id) JOIN department d USING(department_id) JOIN permission p USING(permission_id) JOIN resource r USING(resource_id) ORDER BY l.occurred_at,l.log_id;
