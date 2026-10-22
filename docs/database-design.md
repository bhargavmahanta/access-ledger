# AccessLedger — Relational Schema Design

Scope source: `AccessLedger_Review_1.pdf` (Review 1, 8 pages). This document fixes the
logical design that the PDF only *proposed*, and records every decision made while moving
from the proposal to executable PostgreSQL.

**Status: Review 1 deliverable, frozen against the Review 1 proposal.** No claim in this
document asserts that code has been executed; see `docs/evidence/phase1-run.md` for that.

---

## 1. Design goals

1. One place answers *"who currently has this permission?"* — FR-04.
2. Every evaluated access attempt leaves exactly one immutable audit event — FR-05.
3. Assignment mistakes are rejected by the database, not by application code — FR-03.
4. Audit history survives revocation and deactivation — FR-07.
5. The schema stays at eight relations with no convenience additions.

## 2. The eight relations

Type choices are PostgreSQL-flavoured but map cleanly onto any SQL DBMS.

### DEPARTMENT
| Attribute | Type | Constraints |
|---|---|---|
| department_id | `INTEGER` | PRIMARY KEY, `GENERATED ALWAYS AS IDENTITY` |
| department_name | `VARCHAR(100)` | NOT NULL, UNIQUE |

### APP_USER
| Attribute | Type | Constraints |
|---|---|---|
| user_id | `INTEGER` | PRIMARY KEY, identity |
| department_id | `INTEGER` | NOT NULL, FK → DEPARTMENT(department_id) `ON DELETE RESTRICT` |
| full_name | `VARCHAR(150)` | NOT NULL |
| email | `VARCHAR(254)` | NOT NULL, UNIQUE (on the normalized value — §4) |
| status | `VARCHAR(10)` | NOT NULL DEFAULT `'ACTIVE'`, CHECK ∈ {ACTIVE, DISABLED} |

Each user belongs to exactly one department.

### ROLE
| Attribute | Type | Constraints |
|---|---|---|
| role_id | `INTEGER` | PRIMARY KEY, identity |
| role_name | `VARCHAR(80)` | NOT NULL, UNIQUE |
| is_active | `BOOLEAN` | NOT NULL DEFAULT true |

### USER_ROLE
| Attribute | Type | Constraints |
|---|---|---|
| user_id | `INTEGER` | PK part 1, FK → APP_USER `ON DELETE RESTRICT` |
| role_id | `INTEGER` | PK part 2, FK → ROLE `ON DELETE RESTRICT` |
| assigned_at | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |

PRIMARY KEY (user_id, role_id). The composite key *is* the duplicate-assignment guard —
a second identical row is a primary-key violation, not a separate rule.

### RESOURCE
| Attribute | Type | Constraints |
|---|---|---|
| resource_id | `INTEGER` | PRIMARY KEY, identity |
| resource_code | `VARCHAR(50)` | NOT NULL, UNIQUE |
| name | `VARCHAR(150)` | NOT NULL |
| type | `VARCHAR(30)` | NOT NULL |
| is_active | `BOOLEAN` | NOT NULL DEFAULT true |

### PERMISSION
| Attribute | Type | Constraints |
|---|---|---|
| permission_id | `INTEGER` | PRIMARY KEY, identity |
| resource_id | `INTEGER` | NOT NULL, FK → RESOURCE `ON DELETE RESTRICT` |
| action_code | `VARCHAR(40)` | NOT NULL |

UNIQUE (resource_id, action_code). One row = one action on one resource.

### ROLE_PERMISSION
| Attribute | Type | Constraints |
|---|---|---|
| role_id | `INTEGER` | PK part 1, FK → ROLE `ON DELETE RESTRICT` |
| permission_id | `INTEGER` | PK part 2, FK → PERMISSION `ON DELETE RESTRICT` |
| granted_at | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |

PRIMARY KEY (role_id, permission_id).

### ACCESS_LOG
| Attribute | Type | Constraints |
|---|---|---|
| log_id | `INTEGER` | PRIMARY KEY, identity |
| user_id | `INTEGER` | NOT NULL, FK → APP_USER `ON DELETE RESTRICT` |
| permission_id | `INTEGER` | NOT NULL, FK → PERMISSION `ON DELETE RESTRICT` |
| occurred_at | `TIMESTAMPTZ` | NOT NULL DEFAULT now() |
| decision | `VARCHAR(5)` | NOT NULL, CHECK ∈ {ALLOW, DENY} |
| reason_code | `VARCHAR(25)` | NOT NULL, CHECK — see §4 |

No `resource_id` column: the resource is reached through `permission_id`, and storing it
again would create a second source of truth that can disagree with the permission.

---

## 3. Why two junction tables and not one

`APP_USER` ↔ `ROLE` and `ROLE` ↔ `PERMISSION` are both many-to-many:

- One user may hold Analyst *and* Auditor; one Analyst role is held by many users.
- One role may carry READ *and* WRITE; one WRITE permission is carried by many roles.

A many-to-many relationship has no representation in a single flat relation without either
repeating attributes or storing a list. Both break first normal form:

| Flattened attempt | Why it is invalid |
|---|---|
| `APP_USER(user_id, full_name, email, role_name, …)` | `role_name` depends on `role_id`, not on `user_id`. A user with two roles repeats their own attributes. |
| `APP_USER(user_id, roles TEXT)` | Multi-valued attribute — violates 1NF. |

So each becomes its own relation whose primary key is the composite of the two parent keys.
That makes `user_id → full_name` and `role_id → role_name` each hold inside `USER_ROLE`, and
it makes the duplicate-assignment rule fall out of the primary key for free. See
`normalization.md` §3 for the full derivation.

## 4. Decisions taken while implementing the proposal

The Review 1 PDF states these as open. Each resolution is recorded here with its reason.

### 4.1 Timestamps — one standard (PDF p5 leaves the type pending)

**Decision:** every timestamp is `TIMESTAMPTZ` (stored UTC, rendered in the session zone);
cluster `log_timezone = 'UTC'`.

`TIMESTAMP WITHOUT TIME ZONE` would store a wall-clock reading with no offset, so two
sessions in different zones could order the same event differently. The audit trail is a
chronological record (FR-06); the type has to carry an unambiguous instant.

### 4.2 Email normalization (PDF p5: "normalized before uniqueness checks")

**Decision:** a `BEFORE INSERT OR UPDATE` trigger rewrites `NEW.email := lower(btrim(NEW.email))`,
then a plain `UNIQUE (email)` constraint applies.

Two alternatives were rejected:

- *Expression index* `UNIQUE (lower(btrim(email)))` — no trigger, but the uniqueness rule is
  no longer visible as a table constraint, and any ad-hoc `GROUP BY email` still sees
  un-normalized duplicates.
- *A generated stored column* — works, but adds a ninth visible attribute the Review 1
  attribute list does not contain.

Normalizing the stored value keeps the data itself clean, so equality joins and aggregation
on email are correct, and keeps `UNIQUE` a real constraint faculty can read in `\d app_user`.

### 4.3 `reason_code` controlled vocabulary (PDF requires one; never enumerates it)

**Decision — five codes, one per clause of the access rule:**

| decision | reason_code | clause of the PDF access rule |
|---|---|---|
| ALLOW | `PERMISSION_GRANTED` | all four conditions hold |
| DENY | `USER_DISABLED` | the user is not active |
| DENY | `RESOURCE_INACTIVE` | the resource is not active |
| DENY | `NO_ACTIVE_ROLE` | no assigned role is active |
| DENY | `PERMISSION_NOT_GRANTED` | no active role contains the permission |

The PDF states the rule as a conjunction of four conditions, so four denial causes plus one
success cause is the minimal faithful vocabulary. `decision` and `reason_code` are
cross-checked so an impossible pair (e.g. `ALLOW` + `USER_DISABLED`) cannot be stored:

```sql
CHECK ( (decision = 'ALLOW' AND reason_code = 'PERMISSION_GRANTED')
     OR (decision = 'DENY'  AND reason_code <> 'PERMISSION_GRANTED') )
```

**Known gap, stated plainly:** a *non-existent* user or permission cannot be logged —
`access_log.user_id` and `access_log.permission_id` are mandatory FKs, so there is no legal
row for an unknown actor. Recording such attempts would require either a nullable FK or a
ninth entity, both excluded by the project scope. The access routine therefore rejects an
unknown user or permission as an *error* before evaluation, and the five codes above cover
every denial that can legitimately reach the log. This is a consequence of the mandated
eight-relation model, not an oversight.

### 4.4 `resource.type` is deliberately *not* CHECKed

The PDF lists `DATABASE / APPLICATION / SERVER / DOCUMENT` as *examples*. Resource types are
business vocabulary that grows as the organization adopts new systems; pinning them would
make adding a resource type a schema change. Contrast with `reason_code`, where §7 of the
brief explicitly requires valid reason codes to be constrained. `type` stays a `NOT NULL`
`VARCHAR(30)`.

### 4.5 `ON DELETE RESTRICT` on every foreign key

Stated explicitly rather than left to the default so the intent is readable: a user, role,
resource or permission referenced by an assignment or an audit event cannot be deleted.
Deactivation (`status = 'DISABLED'`, `is_active = false`) is the only route out, which is what
"assignments represent current access only" requires.

### 4.6 Audit protection, and its honest limits

Three layers, because each covers a gap the others leave:

1. `REVOKE UPDATE, DELETE, TRUNCATE ON access_log FROM <app role>` — stops the application's
   database role.
2. `BEFORE UPDATE OR DELETE` trigger on `access_log` raising an exception — also stops the
   **table owner**, whom privileges do not constrain.
3. A `BEFORE UPDATE` trigger on `permission` that freezes `(resource_id, action_code)` once
   the permission is referenced by `access_log`, implementing "resource-action definitions
   become immutable once referenced by logs; new meanings require new permission records".

**Limitations, to be stated in the report:** a superuser can `DROP TRIGGER`, run
`ALTER TABLE access_log DISABLE TRIGGER`, or `SET session_replication_role = replica`, and
`COPY` to a shadow table is invisible to all three. These controls stop ordinary and
privileged-but-not-superuser mistakes. Genuine tamper-proofing needs external
append-only storage or cryptographic chaining, which the Review 1 PDF explicitly places
outside scope.

### 4.7 Surrogate keys throughout, composite keys in the junctions

IDs are stable surrogate keys on the six master relations. The two junctions use the
composite key rather than a surrogate `assignment_id` because the pair *is* the identity of
an assignment — there is nothing else to describe — and the natural key gives duplicate
rejection for free.

---

## 5. Relationship summary

```
DEPARTMENT  1 ─── 0..N APP_USER
APP_USER    1 ─── 0..N USER_ROLE      ──N..1 ROLE
ROLE        1 ─── 0..N ROLE_PERMISSION ──N..1 PERMISSION
RESOURCE    1 ─── 0..N PERMISSION
APP_USER    1 ─── 0..N ACCESS_LOG     ──N..1 PERMISSION
```

Every parent may have zero children; every child references exactly one parent; all
diagrammed foreign keys are required (`NOT NULL`). The diagram is in `er-diagram.md`.

## 6. What this design deliberately does not do

No role inheritance, no direct user→permission grant, no explicit deny rule, no access-request
approval workflow, no multi-tenancy, no direct user-to-resource assignment. Each was
considered and excluded — each would either duplicate an existing fact, add a ninth entity,
or import an approval concept the Review 1 PDF puts outside scope. Adding any of them later
means changing the schema, which is why they are listed rather than quietly available.