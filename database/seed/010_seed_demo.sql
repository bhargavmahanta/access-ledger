-- ============================================================================
-- AccessLedger — synthetic demonstration data
-- ----------------------------------------------------------------------------
-- Deterministic: fixed timestamps, no now(), no random(). Re-running against a
-- populated database fails by design -- ACCESS_LOG is append-only and will not
-- truncate, and the master data is keyed by identity columns. Always rebuild
-- first:  ./scripts/reset-db.sh
--
-- Every person, department, system and event here is invented for the lab.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Departments
-- ----------------------------------------------------------------------------
INSERT INTO department (department_name) VALUES
    ('Computer Science'), ('Finance'), ('Human Resources'), ('Facilities');

-- ----------------------------------------------------------------------------
-- Users -- 8 people; #5 is DISABLED and #8 deliberately holds no role at all
-- (both are needed to demonstrate the denial paths and the no-roles subquery).
-- ----------------------------------------------------------------------------
INSERT INTO app_user (department_id, full_name, email, status)
SELECT d.department_id, v.full_name, v.email, v.status
FROM (VALUES
    ('Computer Science', 'Priya Sharma',   'priya.sharma@uni.edu',   'ACTIVE'),
    ('Computer Science', 'Daniel Okoye',   'daniel.okoye@uni.edu',   'ACTIVE'),
    ('Finance',          'Mei Lin Chen',   'mei.chen@uni.edu',       'ACTIVE'),
    ('Human Resources',  'Tomas Alvarez',  'tomas.alvarez@uni.edu',  'ACTIVE'),
    ('Finance',          'Aisha Bello',    'aisha.bello@uni.edu',    'DISABLED'),
    ('Computer Science', 'Jonas Weber',    'jonas.weber@uni.edu',    'ACTIVE'),
    ('Facilities',       'Fatima Noor',    'fatima.noor@uni.edu',    'ACTIVE'),
    ('Human Resources',  'Chen Wei',       'chen.wei@uni.edu',       'ACTIVE')
) AS v(dept, full_name, email, status)
JOIN department d ON d.department_name = v.dept;

-- ----------------------------------------------------------------------------
-- Roles -- Legacy Contractor is inactive, to demonstrate disabled-role denial
-- ----------------------------------------------------------------------------
INSERT INTO role (role_name, is_active) VALUES
    ('Viewer',             TRUE),
    ('Analyst',            TRUE),
    ('Auditor',            TRUE),
    ('Administrator',      TRUE),
    ('Legacy Contractor',  FALSE);

-- ----------------------------------------------------------------------------
-- Resources -- RES-DOC-04 is inactive, to demonstrate disabled-resource denial
-- ----------------------------------------------------------------------------
INSERT INTO resource (resource_code, name, type, is_active) VALUES
    ('RES-DB-01',  'Reporting Database', 'DATABASE',    TRUE),
    ('RES-APP-02', 'Internal Application','APPLICATION', TRUE),
    ('RES-SRV-03', 'Finance Server',     'SERVER',      TRUE),
    ('RES-DOC-04', 'Legacy Archive',     'DOCUMENT',    FALSE);

-- ----------------------------------------------------------------------------
-- Permissions -- one row per action on one resource
-- ----------------------------------------------------------------------------
INSERT INTO permission (resource_id, action_code)
SELECT r.resource_id, v.action_code
FROM (VALUES
    ('RES-DB-01',  'READ'),
    ('RES-DB-01',  'WRITE'),
    ('RES-DB-01',  'ADMIN'),
    ('RES-APP-02', 'READ'),
    ('RES-APP-02', 'EXECUTE'),
    ('RES-SRV-03', 'READ'),
    ('RES-SRV-03', 'WRITE'),
    ('RES-SRV-03', 'EXECUTE'),
    ('RES-DOC-04', 'READ')
) AS v(resource_code, action_code)
JOIN resource r ON r.resource_code = v.resource_code;

-- ----------------------------------------------------------------------------
-- User <-> Role assignments
-- ----------------------------------------------------------------------------
INSERT INTO user_role (user_id, role_id)
SELECT u.user_id, r.role_id
FROM (VALUES
    ('priya.sharma@uni.edu',  'Viewer'),            -- also Analyst: 2 paths to some perms
    ('priya.sharma@uni.edu',  'Analyst'),
    ('daniel.okoye@uni.edu',  'Auditor'),
    ('mei.chen@uni.edu',      'Analyst'),
    ('mei.chen@uni.edu',      'Administrator'),    -- union of 2 roles
    ('tomas.alvarez@uni.edu', 'Viewer'),
    ('aisha.bello@uni.edu',   'Analyst'),          -- user is DISABLED
    ('jonas.weber@uni.edu',   'Viewer'),
    ('jonas.weber@uni.edu',   'Auditor'),
    ('jonas.weber@uni.edu',   'Legacy Contractor'),-- role is inactive
    ('fatima.noor@uni.edu',   'Viewer'),
    ('chen.wei@uni.edu',      NULL)                -- no roles at all
) AS v(email, role_name)
JOIN app_user u ON u.email = v.email
JOIN role     r ON r.role_name = v.role_name;

-- ----------------------------------------------------------------------------
-- Role <-> Permission assignments
-- ----------------------------------------------------------------------------
INSERT INTO role_permission (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM (VALUES
    ('Viewer',            'RES-DB-01',  'READ'),
    ('Viewer',            'RES-APP-02', 'READ'),
    ('Viewer',            'RES-DOC-04', 'READ'),
    ('Analyst',           'RES-DB-01',  'READ'),    -- duplicate path vs Viewer
    ('Analyst',           'RES-DB-01',  'WRITE'),
    ('Analyst',           'RES-APP-02', 'EXECUTE'),
    ('Analyst',           'RES-SRV-03', 'READ'),
    ('Auditor',           'RES-DB-01',  'READ'),
    ('Auditor',           'RES-SRV-03', 'READ'),
    ('Auditor',           'RES-DOC-04', 'READ'),
    ('Administrator',     'RES-DB-01',  'ADMIN'),   -- Administrator holds everything
    ('Legacy Contractor', 'RES-DB-01',  'READ'),
    ('Legacy Contractor', 'RES-SRV-03', 'READ')
) AS v(role_name, resource_code, action_code)
JOIN role       r ON r.role_name      = v.role_name
JOIN permission p ON p.action_code    = v.action_code
JOIN resource   s ON s.resource_id    = p.resource_id
                AND s.resource_code  = v.resource_code;

-- ----------------------------------------------------------------------------
-- Recorded access events (FR-05)
-- ----------------------------------------------------------------------------
-- decision is GENERATED from reason_code, so this insert states only the cause
-- and the database derives the outcome -- see database-design.md 4.3.
--
-- The history is deliberately NOT a pure function of the current graph: Tomas
-- accessed RES-DB-01 in February, and the Auditor role holding that permission
-- was reassigned in March. Past events stay true after revocation (FR-07).
INSERT INTO access_log (user_id, permission_id, occurred_at, reason_code)
SELECT u.user_id, p.permission_id, v.occurred_at::timestamptz, v.reason_code
FROM (VALUES
    -- January: baseline traffic
    ('priya.sharma@uni.edu',  'RES-DB-01',  'READ',    '2026-01-05 08:12:00+00', 'PERMISSION_GRANTED'),
    ('priya.sharma@uni.edu',  'RES-DB-01',  'WRITE',   '2026-01-05 08:19:00+00', 'PERMISSION_GRANTED'),
    ('priya.sharma@uni.edu',  'RES-DB-01',  'ADMIN',   '2026-01-05 08:24:00+00', 'PERMISSION_NOT_GRANTED'),
    ('daniel.okoye@uni.edu',  'RES-DB-01',  'READ',    '2026-01-06 09:02:00+00', 'PERMISSION_GRANTED'),
    ('daniel.okoye@uni.edu',  'RES-DOC-04', 'READ',    '2026-01-06 09:07:00+00', 'RESOURCE_INACTIVE'),
    ('tomas.alvarez@uni.edu', 'RES-APP-02', 'READ',    '2026-01-07 10:31:00+00', 'PERMISSION_GRANTED'),
    ('aisha.bello@uni.edu',   'RES-DB-01',  'READ',    '2026-01-08 11:15:00+00', 'USER_DISABLED'),
    ('aisha.bello@uni.edu',   'RES-SRV-03', 'WRITE',   '2026-01-08 11:18:00+00', 'USER_DISABLED'),
    ('chen.wei@uni.edu',      'RES-DB-01',  'READ',    '2026-01-09 13:44:00+00', 'NO_ACTIVE_ROLE'),
    ('fatima.noor@uni.edu',   'RES-SRV-03', 'EXECUTE', '2026-01-09 14:02:00+00', 'PERMISSION_NOT_GRANTED'),

    -- February: denied-attempt pattern for one user (FR-06 reporting demo)
    ('tomas.alvarez@uni.edu', 'RES-DB-01',  'READ',    '2026-02-02 08:55:00+00', 'PERMISSION_NOT_GRANTED'),
    ('tomas.alvarez@uni.edu', 'RES-DB-01',  'WRITE',   '2026-02-02 08:56:00+00', 'PERMISSION_NOT_GRANTED'),
    ('tomas.alvarez@uni.edu', 'RES-DB-01',  'ADMIN',   '2026-02-02 08:57:00+00', 'PERMISSION_NOT_GRANTED'),
    ('tomas.alvarez@uni.edu', 'RES-SRV-03', 'EXECUTE', '2026-02-03 15:20:00+00', 'PERMISSION_NOT_GRANTED'),
    ('tomas.alvarez@uni.edu', 'RES-DB-01',  'READ',    '2026-02-11 09:41:00+00', 'PERMISSION_NOT_GRANTED'),
    ('tomas.alvarez@uni.edu', 'RES-DB-01',  'WRITE',   '2026-02-11 09:42:00+00', 'PERMISSION_NOT_GRANTED'),

    -- March: multi-role union in action
    ('mei.chen@uni.edu',      'RES-DB-01',  'ADMIN',   '2026-03-04 09:00:00+00', 'PERMISSION_GRANTED'),
    ('mei.chen@uni.edu',      'RES-SRV-03', 'EXECUTE', '2026-03-04 09:06:00+00', 'PERMISSION_GRANTED'),
    ('mei.chen@uni.edu',      'RES-DOC-04', 'READ',    '2026-03-04 09:09:00+00', 'RESOURCE_INACTIVE'),
    ('mei.chen@uni.edu',      'RES-DB-01',  'READ',    '2026-03-05 11:30:00+00', 'PERMISSION_GRANTED'),
    ('priya.sharma@uni.edu',  'RES-APP-02', 'EXECUTE', '2026-03-05 11:44:00+00', 'PERMISSION_GRANTED'),
    ('priya.sharma@uni.edu',  'RES-DB-01',  'READ',    '2026-03-06 08:05:00+00', 'PERMISSION_GRANTED'),

    -- April: role deactivation takes effect
    ('jonas.weber@uni.edu',   'RES-DB-01',  'READ',    '2026-04-01 08:30:00+00', 'PERMISSION_GRANTED'),
    ('jonas.weber@uni.edu',   'RES-SRV-03', 'READ',    '2026-04-01 08:33:00+00', 'NO_ACTIVE_ROLE'),
    ('jonas.weber@uni.edu',   'RES-SRV-03', 'WRITE',   '2026-04-01 08:35:00+00', 'NO_ACTIVE_ROLE'),
    ('daniel.okoye@uni.edu',  'RES-APP-02', 'READ',    '2026-04-02 10:12:00+00', 'PERMISSION_NOT_GRANTED'),
    ('fatima.noor@uni.edu',   'RES-DB-01',  'READ',    '2026-04-02 10:20:00+00', 'PERMISSION_GRANTED'),
    ('fatima.noor@uni.edu',   'RES-DB-01',  'WRITE',   '2026-04-02 10:21:00+00', 'PERMISSION_NOT_GRANTED'),
    ('daniel.okoye@uni.edu',  'RES-DOC-04', 'READ',    '2026-04-03 16:40:00+00', 'RESOURCE_INACTIVE'),
    ('tomas.alvarez@uni.edu', 'RES-APP-02', 'READ',    '2026-04-03 16:44:00+00', 'PERMISSION_GRANTED'),

    -- May: repeated identical attempts -- FR-05 requires each to survive as its
    -- own log_id even though every row is identical apart from time.
    ('chen.wei@uni.edu',      'RES-DB-01',  'READ',    '2026-05-12 09:00:00+00', 'NO_ACTIVE_ROLE'),
    ('chen.wei@uni.edu',      'RES-DB-01',  'READ',    '2026-05-12 09:00:30+00', 'NO_ACTIVE_ROLE'),
    ('chen.wei@uni.edu',      'RES-DB-01',  'READ',    '2026-05-12 09:01:00+00', 'NO_ACTIVE_ROLE'),
    ('chen.wei@uni.edu',      'RES-DB-01',  'READ',    '2026-05-12 09:01:30+00', 'NO_ACTIVE_ROLE'),
    ('mei.chen@uni.edu',      'RES-DB-01',  'ADMIN',   '2026-05-18 14:22:00+00', 'PERMISSION_GRANTED'),
    ('mei.chen@uni.edu',      'RES-DB-01',  'ADMIN',   '2026-05-18 14:22:10+00', 'PERMISSION_GRANTED'),
    ('priya.sharma@uni.edu',  'RES-SRV-03', 'EXECUTE', '2026-05-20 07:55:00+00', 'PERMISSION_NOT_GRANTED'),
    ('jonas.weber@uni.edu',   'RES-APP-02', 'READ',    '2026-05-21 12:10:00+00', 'PERMISSION_GRANTED')
) AS v(email, resource_code, action_code, occurred_at, reason_code)
JOIN app_user   u ON u.email        = v.email
JOIN permission p ON p.action_code  = v.action_code
JOIN resource   s ON s.resource_id  = p.resource_id
                AND s.resource_code = v.resource_code;

COMMIT;