-- Complete demo seed: apply once to an empty migrated database. Audit events are genuine evaluations.
SELECT policy_lock();
INSERT INTO department (department_name) VALUES
    ('Computer Science'), ('Finance'), ('Human Resources'), ('Facilities'), ('Engineering'), ('Security'), ('Operations'), ('Legal'), ('Research'), ('Support');

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
    ('Finance',          'Aisha Bello',    'aisha.bello@uni.edu',    'ACTIVE'),
    ('Computer Science', 'Jonas Weber',    'jonas.weber@uni.edu',    'ACTIVE'),
    ('Facilities',       'Fatima Noor',    'fatima.noor@uni.edu',    'ACTIVE'),
    ('Human Resources',  'Chen Wei',       'chen.wei@uni.edu',       'ACTIVE')
) AS v(dept, full_name, email, status)
JOIN department d ON d.department_name = v.dept ORDER BY v.email;

-- ----------------------------------------------------------------------------
-- Roles -- Legacy Contractor is inactive, to demonstrate disabled-role denial
-- ----------------------------------------------------------------------------
INSERT INTO role (role_name, is_active) VALUES
    ('Viewer',             TRUE),
    ('Analyst',            TRUE),
    ('Auditor',            TRUE),
    ('Administrator',      TRUE),
    ('Legacy Contractor', TRUE), ('Developer',TRUE), ('Database Administrator',TRUE), ('HR Manager',TRUE), ('Finance Analyst',TRUE), ('Intern',TRUE);

-- ----------------------------------------------------------------------------
-- Resources -- RES-DOC-04 is inactive, to demonstrate disabled-resource denial
-- ----------------------------------------------------------------------------
INSERT INTO resource (resource_code, name, type, is_active) VALUES
    ('RES-DB-01',  'Reporting Database', 'DATABASE',    TRUE),
    ('RES-APP-02', 'Internal Application','APPLICATION', TRUE),
    ('RES-SRV-03', 'Finance Server',     'SERVER',      TRUE),
    ('RES-DOC-04', 'Legacy Archive',     'DOCUMENT',    TRUE);

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
JOIN resource r ON r.resource_code = v.resource_code ORDER BY r.resource_id,v.action_code;

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


INSERT INTO app_user(department_id,full_name,email) VALUES(10,'Rahul Verma','rahul.verma@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(1,'Nora Patel','nora.patel@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(2,'Omar Hassan','omar.hassan@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(3,'Elena Rossi','elena.rossi@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(4,'Lucas Silva','lucas.silva@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(5,'Hana Kim','hana.kim@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(6,'Arjun Rao','arjun.rao@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(7,'Sofia Garcia','sofia.garcia@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(8,'Noah Brown','noah.brown@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(9,'Leila Khan','leila.khan@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(10,'Maya Das','maya.das@uni.edu');
INSERT INTO app_user(department_id,full_name,email) VALUES(1,'Ethan Lee','ethan.lee@uni.edu');
INSERT INTO resource(resource_code,name,type) VALUES('RES-05','Employee Directory','DATABASE');
INSERT INTO resource(resource_code,name,type) VALUES('RES-06','Deployment Console','APPLICATION');
INSERT INTO resource(resource_code,name,type) VALUES('RES-07','Build Server','SERVER');
INSERT INTO resource(resource_code,name,type) VALUES('RES-08','Security Handbook','DOCUMENT');
INSERT INTO resource(resource_code,name,type) VALUES('RES-09','Payroll Database','DATABASE');
INSERT INTO resource(resource_code,name,type) VALUES('RES-10','Support Portal','APPLICATION');
INSERT INTO resource(resource_code,name,type) VALUES('RES-11','Research Server','SERVER');
INSERT INTO resource(resource_code,name,type) VALUES('RES-12','Policy Library','DOCUMENT');
INSERT INTO permission(resource_id,action_code) SELECT r.resource_id,a.action FROM resource r CROSS JOIN (VALUES('READ'),('WRITE'),('EXECUTE')) a(action) WHERE r.resource_code LIKE 'RES-%' AND r.resource_id>=5;
INSERT INTO role_permission(role_id,permission_id) SELECT r.role_id,p.permission_id FROM role r CROSS JOIN permission p WHERE r.role_name='Administrator' ON CONFLICT DO NOTHING;
INSERT INTO role_permission(role_id,permission_id) SELECT r.role_id,p.permission_id FROM role r CROSS JOIN permission p JOIN resource s USING(resource_id) WHERE (r.role_name='Developer' AND s.resource_code='RES-APP-02') OR (r.role_name='Database Administrator' AND s.type='DATABASE') OR (r.role_name='HR Manager' AND s.resource_code='RES-05') OR (r.role_name='Finance Analyst' AND s.resource_code='RES-SRV-03');
INSERT INTO user_role(user_id,role_id) SELECT u.user_id,r.role_id FROM app_user u CROSS JOIN role r WHERE u.email='rahul.verma@uni.edu' AND r.role_name='Developer';
INSERT INTO user_role(user_id,role_id) SELECT u.user_id,r.role_id FROM app_user u CROSS JOIN role r WHERE u.user_id>=10 AND r.role_name IN ('Viewer','Analyst') ON CONFLICT DO NOTHING;
INSERT INTO user_role(user_id,role_id) SELECT u.user_id,r.role_id FROM app_user u CROSS JOIN role r WHERE u.email='ethan.lee@uni.edu' AND r.role_name='Intern';
DO $$
DECLARE v_user integer; v_role integer; v_permission integer;
BEGIN
 SELECT user_id INTO v_user FROM app_user WHERE email='aisha.bello@uni.edu';
 CALL set_user_status(v_user,'DISABLED');
 SELECT role_id INTO v_role FROM role WHERE role_name='Legacy Contractor';
 CALL set_role_active(v_role,false);
 CALL set_resource_active(4,false);
 SELECT user_id INTO v_user FROM app_user WHERE email='rahul.verma@uni.edu';
 SELECT role_id INTO v_role FROM role WHERE role_name='Developer';
 SELECT p.permission_id INTO v_permission FROM permission p JOIN resource r USING(resource_id)
 WHERE r.resource_code='RES-APP-02' AND p.action_code='READ';
 PERFORM evaluate_access(v_user,v_permission);
 CALL revoke_user_role(v_user,v_role);
 PERFORM evaluate_access(v_user,v_permission);
END $$;
SELECT e.* FROM generate_series(1,118) AS g(i) CROSS JOIN LATERAL evaluate_access(((g.i-1)%20)+1,((g.i-1)%33)+1) e;
