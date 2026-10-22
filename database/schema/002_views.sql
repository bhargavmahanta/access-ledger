-- ============================================================================
-- 002 — Views (Review 1 section 9)
-- ----------------------------------------------------------------------------
-- Derived read models. Every one is a pure projection of the eight base
-- relations -- no view stores anything, and none can disagree with its source.
-- Run after 001_core_schema.sql:  psql -f database/schema/002_views.sql
-- ============================================================================

BEGIN;

DROP VIEW IF EXISTS vw_denied_access_attempts;
DROP VIEW IF EXISTS vw_access_audit_history;
DROP VIEW IF EXISTS vw_resource_access_summary;
DROP VIEW IF EXISTS vw_effective_user_permissions;
DROP VIEW IF EXISTS vw_active_users_with_roles;

-- 1. Active users with assigned roles -----------------------------------------
-- Answers "who is currently participating in the access model at all", and is
-- the LEFT JOIN that keeps role-less users out.
CREATE VIEW vw_active_users_with_roles AS
SELECT u.user_id,
       u.full_name,
       u.email,
       d.department_id,
       d.department_name,
       r.role_id,
       r.role_name
FROM       app_user u
JOIN       department d  ON d.department_id = u.department_id
JOIN       user_role ur  ON ur.user_id      = u.user_id
JOIN       role      r   ON r.role_id       = ur.role_id
WHERE      u.status = 'ACTIVE'
  AND      r.is_active;


-- 2. Effective user permissions (FR-04) ---------------------------------------
-- One row per (user, permission). The role that supplied it is deliberately NOT
-- exposed: a user reaching one permission through two roles must collapse to one
-- row, which is what DISTINCT enforces here and what makes UNION semantics
-- observable. resource_name is sourced from RESOURCE, never from a duplicate
-- column, so the view cannot contradict the permission it names.
CREATE VIEW vw_effective_user_permissions AS
SELECT DISTINCT
       u.user_id,
       u.email,
       u.full_name,
       p.permission_id,
       s.resource_id,
       s.resource_code,
       s.name     AS resource_name,
       s.type     AS resource_type,
       p.action_code
FROM       app_user         u
JOIN       user_role        ur ON ur.user_id       = u.user_id
JOIN       role             r  ON r.role_id        = ur.role_id
JOIN       role_permission  rp ON rp.role_id       = r.role_id
JOIN       permission       p  ON p.permission_id  = rp.permission_id
JOIN       resource         s  ON s.resource_id    = p.resource_id
WHERE      u.status = 'ACTIVE'
  AND      r.is_active
  AND      s.is_active;


-- 3. Resource access summary --------------------------------------------------
CREATE VIEW vw_resource_access_summary AS
SELECT s.resource_id,
       s.resource_code,
       s.name         AS resource_name,
       s.type         AS resource_type,
       s.is_active,
       COUNT(DISTINCT p.permission_id)   AS defined_actions,
       COUNT(DISTINCT rp.role_id)        AS roles_referencing,
       COUNT(DISTINCT ur.user_id)        AS users_with_any_role_path,
       COUNT(l.log_id)                   AS attempts,
       COUNT(*) FILTER (WHERE l.decision = 'DENY') AS denied
FROM       resource        s
LEFT JOIN  permission       p  ON p.resource_id    = s.resource_id
LEFT JOIN  role_permission  rp ON rp.permission_id = p.permission_id
LEFT JOIN  user_role        ur ON ur.role_id       = rp.role_id
LEFT JOIN  access_log       l  ON l.permission_id  = p.permission_id
GROUP BY   s.resource_id, s.resource_code, s.name, s.type, s.is_active;


-- 4. Access audit history (FR-05, FR-06) --------------------------------------
-- Fully flattened event stream: every log row resolvable to human-readable
-- context without the caller writing the joins.
CREATE VIEW vw_access_audit_history AS
SELECT l.log_id,
       l.occurred_at,
       l.decision,
       l.reason_code,
       u.user_id,
       u.email,
       u.full_name,
       d.department_name,
       p.permission_id,
       s.resource_code,
       s.name     AS resource_name,
       s.type     AS resource_type,
       p.action_code
FROM       access_log  l
JOIN       app_user    u ON u.user_id       = l.user_id
JOIN       department  d ON d.department_id = u.department_id
JOIN       permission  p ON p.permission_id = l.permission_id
JOIN       resource    s ON s.resource_id   = p.resource_id;


-- 5. Denied access attempts ---------------------------------------------------
CREATE VIEW vw_denied_access_attempts AS
SELECT * FROM vw_access_audit_history WHERE decision = 'DENY';

COMMIT;