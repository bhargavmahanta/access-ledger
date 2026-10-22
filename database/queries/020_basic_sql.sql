-- Legitimate department lifecycle. Rollback makes the demonstration repeatable.
BEGIN;
\echo 'INSERT: register an unused department'
INSERT INTO department(department_name) VALUES('Temporary Training Department') RETURNING *;
\echo 'UPDATE: correct its name'
UPDATE department SET department_name='Temporary Learning Department' WHERE department_name='Temporary Training Department' RETURNING *;
\echo 'DELETE: remove an unused department (referenced departments are protected)'
DELETE FROM department WHERE department_name='Temporary Learning Department' RETURNING *;
ROLLBACK;
