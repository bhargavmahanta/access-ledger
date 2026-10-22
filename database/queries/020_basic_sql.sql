-- ============================================================================
-- 020 — Basic SQL: DDL, DML, SELECT, WHERE, ORDER BY, DISTINCT
-- Run after the seed:  psql -f database/queries/020_basic_sql.sql
-- ============================================================================

\echo '--- CREATE TABLE / ALTER TABLE (on a scratch table, so the design is untouched) ---'
CREATE TABLE demo_note (
    note_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    body     VARCHAR(200) NOT NULL,
    severity VARCHAR(10)
);
ALTER TABLE demo_note ADD CONSTRAINT ck_demo_note_severity
    CHECK (severity IN ('LOW', 'HIGH'));
\echo '   created demo_note and added ck_demo_note_severity'

\echo ''
\echo '--- INSERT ---'
INSERT INTO demo_note (body, severity) VALUES
    ('index rebuild queued', 'LOW'),
    ('revocation delayed',   'HIGH'),
    ('stale role cache',     'HIGH');

\echo ''
\echo '--- UPDATE ---'
UPDATE demo_note SET severity = 'LOW' WHERE body = 'stale role cache'
    RETURNING note_id, body, severity;

\echo ''
\echo '--- SELECT ... WHERE ... ORDER BY ---'
SELECT note_id, body, severity
FROM   demo_note
WHERE  severity = 'LOW'
ORDER  BY body;

\echo ''
\echo '--- SELECT with a computed expression ---'
SELECT rpad(role_name, 18) AS role,
       is_active,
       CASE WHEN is_active THEN 'usable for access decisions'
            ELSE 'denies everything until reactivated' END AS effect
FROM   role ORDER BY is_active DESC, role_name;

\echo ''
\echo '--- DISTINCT: which action codes actually exist, and how often ---'
SELECT   DISTINCT p.action_code
FROM     permission p
ORDER    BY p.action_code;

\echo ''
\echo '--- DELETE (permitted here; the same statement is refused on access_log) ---'
DELETE FROM demo_note WHERE severity = 'LOW' RETURNING note_id, body;
\echo '   compare: DELETE FROM access_log ... is rejected -- see docs/evidence/phase1-run.md'

\echo ''
\echo '--- DELETE on an audit-referenced parent is refused by ON DELETE RESTRICT ---'
DO $$
BEGIN
    DELETE FROM permission WHERE action_code = 'READ' AND resource_id =
        (SELECT resource_id FROM resource WHERE resource_code = 'RES-DB-01');
    RAISE NOTICE 'unexpectedly succeeded';
EXCEPTION WHEN foreign_key_violation THEN
    RAISE NOTICE 'refused as expected: %', SQLERRM;
END $$;

DROP TABLE demo_note;