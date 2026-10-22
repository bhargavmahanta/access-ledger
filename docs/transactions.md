# Transactions and concurrency

Every valid access evaluation is one VOLATILE PL/pgSQL function invocation that checks policy and inserts one event. The API commits its write transaction before returning a successful decision. An insertion error or commit error returns no successful ALLOW and leaves no partially committed event. A disconnected client after commit may retry and create another legitimate event; the model intentionally has no idempotency table.

## Lock protocol

Use transaction-scoped advisory key (302,8). Evaluations acquire a shared lock; all controlled policy mutations acquire an exclusive lock. Locks release on transaction commit/rollback. Concurrent evaluations may proceed together, while any mutation waits for in-flight evaluations. Mutations obtain the lock before reading/checking/changing a row, consistently avoiding lock-order inversions between controlled operations. Callers must not upgrade a shared evaluation transaction into a policy-mutation transaction; each API mutation/evaluation uses its own short transaction.

The global key simplifies proof for a small academic system: user status, user-role assignment/revocation, role activation, permission grant/removal, resource activation and permission identity changes cannot be overlooked by separate row-lock paths. It sacrifices write concurrency across unrelated users. Row locking could increase parallelism but would require a more complicated fixed ordering across the authorization graph and protection against newly inserted role paths.

READ COMMITTED is required and checked inside policy_lock. evaluate_access is VOLATILE and uses separate internal statements: obtain the lock first, then read users/resources/role paths using fresh snapshots. A function-wide snapshot frozen before waiting would be incorrect. Unsupported transaction isolation raises 25000 before policy reads. The effective-permission read function is a normal snapshot report and does not create an authorization decision.

## Protected entry points

assign_user_role, revoke_user_role, grant_role_permission, revoke_role_permission, set_user_status, set_role_active, set_resource_active, update_permission_identity and management creation/edit functions all use the same lock before any table access. The application cannot bypass them with direct DML. Maintenance SQL executed by the owner/superuser must call policy_lock(false) before direct writes; privileged bypass is outside the guarantee. Normal migrations and seeding are administrative maintenance activities.

## Proven schedules

The automated suite opens separate real application-login connections. In the evaluation-first schedule, mutation blocks until the ALLOW event commits, then subsequent evaluation denies. In the writer-first schedule, evaluation blocks until the mutation commits and sees the committed change. Tests observe pg_stat_activity's advisory wait event rather than relying on arbitrary delays. These schedules cover assignment revocation, role deactivation, permission removal, user disabling and resource disabling. A barrier test requires two evaluations to obtain shared locks before either can commit, then verifies two distinct persistent events.

## Direct demonstrations

Use `database/queries/020_basic_sql.sql` for a rolled-back department INSERT/UPDATE/DELETE lifecycle. `scripts/verification/capture-evidence.py` records the controlled assignment, permission grant, ALLOW, revocation, DENY and retained-history workflow in a disposable verification database. Database tests cover successful commit, explicit rollback, duplicate assignment, FK rejection and injected audit-insert failure. Audit sequence gaps after rollback are expected PostgreSQL sequence behavior, not missing committed audit records.
