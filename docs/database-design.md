# Relational design and implementation decisions

The pasted AccessLedger master prompt is the available requirements source. Referenced faculty PDFs are absent. Historical evidence describes the earlier prototype only.

## Eight core relations

| Relation | Primary key | Other candidate key | Required references / attributes |
|---|---|---|---|
| DEPARTMENT | department_id | department_name | department_name |
| APP_USER | user_id | normalized email | department_id → DEPARTMENT; full_name, email, status |
| ROLE | role_id | role_name | role_name, is_active |
| USER_ROLE | (user_id, role_id) | — | both parent FKs; assigned_at |
| RESOURCE | resource_id | resource_code | resource_code, name, type, is_active |
| PERMISSION | permission_id | (resource_id, action_code) | resource_id → RESOURCE; action_code |
| ROLE_PERMISSION | (role_id, permission_id) | — | both parent FKs; granted_at |
| ACCESS_LOG | log_id | — | user_id → APP_USER; permission_id → PERMISSION; occurred_at, generated decision, reason_code |

All FK columns and required attributes are NOT NULL. All FKs use ON DELETE RESTRICT. Junction primary keys reject duplicate pairs. Single-column primary keys are GENERATED ALWAYS AS IDENTITY integers. Master names/codes have UNIQUE constraints where shown. Email is trimmed and lowercased by a BEFORE trigger before uniqueness is checked. Identical access attempts remain distinct events.

## Domains and defaults

User status is ACTIVE or DISABLED (default ACTIVE); role/resource activation defaults true. Resource type is an open nonempty vocabulary in the API; DATABASE, APPLICATION, SERVER and DOCUMENT are the demo choices. SQL stores VARCHAR(30) NOT NULL without a closed type enumeration. Timestamps are TIMESTAMPTZ with default now(); evaluate_access uses clock_timestamp() after obtaining its lock so the recorded instant is the evaluation time rather than transaction start. API timestamps include offsets; the interface renders them in the browser's timezone and labels this convention.

Valid persisted reasons are PERMISSION_GRANTED, USER_DISABLED, RESOURCE_INACTIVE, NO_ACTIVE_ROLE, PERMISSION_NOT_GRANTED. The only ALLOW reason is PERMISSION_GRANTED. PostgreSQL generates decision from reason_code, but that alone cannot prevent forged events: the restricted application login has no direct INSERT privilege on ACCESS_LOG. Only evaluate_access can write on its behalf. Invalid references return unlogged DENY with USER_NOT_FOUND or PERMISSION_NOT_FOUND.

## Derived reporting and retention

Effective permissions are distinct over active users, assigned active roles and active resources. Resource event totals are aggregated before joining assignment counts, so many role paths cannot multiply events. Existing vw_* names are preserved; the denied-summary view is added.

Audit UPDATE, DELETE and TRUNCATE are denied both by privileges and triggers. Permission resource/action identity freezes after its first logged event. Current assignments can be revoked without deleting any history. Labels (employee name, department, resource name) are current joined values, not historical snapshots. The model stores historical decisions, not policy-change provenance or labels at the time of an event.

## Ownership and reproducibility

Versioned Alembic migrations execute the canonical SQL files. After a revision is verified and committed its referenced SQL definitions are immutable; changes use another revision and another SQL file. SQLAlchemy is the Python connectivity/query layer, never an alternative schema generator. Alembic's version table lives in infrastructure; public contains exactly eight application tables.

accessledger_demo_owner owns the application objects and cannot log in. accessledger_demo_app is a non-superuser login with SELECT and explicitly granted routine execution. It cannot write policy/audit tables, create public objects, or call the internal policy_lock helper. Routine search_path is pg_catalog, public, pg_temp; public CREATE is revoked from PUBLIC. The original accessledger_app role is untouched.

The private socket cluster uses local trust authentication and is for this trusted machine only. Compose uses passwords and loopback networking. Neither the API nor this demonstration claims production authentication, external-resource enforcement or absolute tamper-proofing. The cluster superuser can bypass these protections.
