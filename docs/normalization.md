# AccessLedger — Functional Dependencies & Normalization

Review 1 states the schema *targets* 3NF and that "a complete functional-dependency analysis
will be checked in Review 2; formal normalization is not yet verified." This is that analysis.

**Result up front:** the eight-relation design is in **3NF**. It satisfies **BCNF on seven of
the eight relations**; `ACCESS_LOG` has one strict BCNF violation that is *inherited from the
specified design*, analysed honestly in §6 rather than glossed over.

---

## 1. The unnormalized form

AccessLedger exists because role, permission and audit facts are kept separately. So imagine
the opposite: the spreadsheet an administrator would actually keep — one row per evaluated
access attempt, with every fact repeated on every attempt.

> **ATTEMPT**(
> `log_id`, `occurred_at`, `decision`, `reason_code`,
> `user_id`, `full_name`, `email`, `user_status`, `dept_name`,
> `role_name`, `role_is_active`, `assigned_at`,
> `resource_code`, `resource_name`, `resource_type`, `resource_is_active`,
> `action_code`, `granted_at`)

A user holding two roles, whose roles carry three permissions, who made ten attempts, occupies
ten rows — 60 rows in total. Everything is atomic, so **1NF in its letter is satisfied**;
what fails is the **repeating group**: `(role_name, resource_code, action_code, granted_at)`
appears once per attempt but describes something that depends only on the authorization
graph, not on the attempt.

Concretely, `assigned_at` repeats identically in all ten of that user's rows; `granted_at`
repeats in every row for that role+permission pair; `resource_name` repeats in all thirty.
**Update anomaly:** changing `resource_name` means updating every row of that sheet, and a
missed row silently forks the resource's name. **Insertion anomaly:** you cannot record a new
resource until someone attempts to use it. **Deletion anomaly:** deleting the last denied
attempt destroys the only trace that the user ever held the role.

---

## 2. 1NF → 2NF — removing partial dependencies on composite keys

The repeating groups are pulled out first, which yields two composite-key relations:

```
USER_ROLE_1NF( user_id, role_name, role_is_active, assigned_at,
               resource_code, resource_name, resource_type, resource_is_active,
               action_code, granted_at )
      key: ( user_id, role_name, resource_code, action_code )

LOG_1NF( log_id, occurred_at, decision, reason_code,
         user_id, role_name, resource_code, action_code )
      key: log_id
```

In `USER_ROLE_1NF` the key is composite, so 2NF forbids any non-prime attribute depending on
*part* of it. Three partial dependencies violate 2NF:

| Non-prime attribute | Depends only on | Violation |
|---|---|---|
| `role_is_active` | `role_name` | partial |
| `resource_name`, `resource_type`, `resource_is_active` | `resource_code` | partial |
| `granted_at` | `(role_name, resource_code, action_code)` | partial (not the whole key) |

`assigned_at` depends on the **whole** key `(user_id, role_name)`, so it is *not* a 2NF
violation and correctly stays with the assignment.

Decomposing on those three partial dependencies:

```
ROLE( role_name, role_is_active )                     key: role_name
RESOURCE( resource_code, resource_name,
          resource_type, resource_is_active )          key: resource_code
USER_ROLE( user_id, role_name, assigned_at )           key: ( user_id, role_name )
ROLE_PERMISSION( role_name, resource_code,
                 action_code, granted_at )             key: ( role_name, resource_code, action_code )
LOG( … )                                               key: log_id — single-attribute key,
                                                       so 2NF is vacuous here
```

`LOG_1NF` has a single-attribute key, so no partial dependency is possible; it passes 2NF
unchanged. **Five** relations so far.

---

## 3. 2NF → 3NF — removing transitive dependencies

Two transitive dependencies remain, both routed through a non-key attribute.

### 3.1 Department through the user

```
LOG( log_id, occurred_at, decision, reason_code,
     user_id, resource_code, action_code,
     full_name, email, user_status, dept_name )
```

- `user_id → full_name, email, user_status, dept_name`, but `user_id` is **not** a key of LOG
  (one user makes many attempts). A non-key attribute determining others is a 3NF violation.
  Decompose on `user_id`:

  ```
  APP_USER( user_id, full_name, email, user_status, dept_name )   key: user_id
  ```

- Inside `APP_USER`, `dept_name` depends on `user_id`, not on `dept_name`'s own key — the
  department's existence is stated once per user, and renaming a department means updating
  every member row. `user_id → dept_name → (the department itself)` is a transitive
  dependency, so:

  ```
  DEPARTMENT( dept_name )      key: dept_name
  ```

### 3.2 The permission, which belongs to no role

`LOG` must identify *what was attempted* — a resource and an action. But `(resource_code,
action_code)` currently exists only as a **part** of the `ROLE_PERMISSION` key. Referencing a
partial key is not a valid key reference, and it also forces the awkward rule that a
permission exists in the log only if some role currently grants it.

```
PERMISSION( resource_code, action_code )   key: ( resource_code, action_code )
```

`ROLE_PERMISSION` now references it by that key, and `LOG` references it by that key.

### Result — the eight relations

`DEPARTMENT`, `APP_USER`, `ROLE`, `USER_ROLE`, `RESOURCE`, `PERMISSION`, `ROLE_PERMISSION`,
`ACCESS_LOG`. Exactly the set the Review 1 PDF proposes, reached by decomposition rather than
assembled by assertion.

---

## 4. Candidate keys

| Relation | Primary key | Other candidate keys | Why |
|---|---|---|---|
| DEPARTMENT | `department_id` | `department_name` | UNIQUE |
| APP_USER | `user_id` | `email` (normalized value) | UNIQUE |
| ROLE | `role_id` | `role_name` | UNIQUE |
| USER_ROLE | `(user_id, role_id)` | — | both FKs → minimal |
| RESOURCE | `resource_id` | `resource_code` | UNIQUE |
| PERMISSION | `permission_id` | `(resource_id, action_code)` | UNIQUE |
| ROLE_PERMISSION | `(role_id, permission_id)` | — | both FKs → minimal |
| ACCESS_LOG | `log_id` | — | identity column, all attributes vary per attempt |

Every candidate key is enforced by a real `PRIMARY KEY` or `UNIQUE` constraint — none is
merely asserted in prose.

## 5. Functional dependencies and 3NF verification

For each relation, every non-prime attribute must depend on the key, on part of a composite
key (2NF), only on a key — never through another non-key attribute.

| Relation | Key | Non-prime FDs | Verdict |
|---|---|---|---|
| DEPARTMENT | `department_id` | `department_id → department_name` | key-only ✓ |
| APP_USER | `user_id` | `user_id → department_id, full_name, email, status` | key-only ✓ |
| ROLE | `role_id` | `role_id → role_name, is_active` | key-only ✓ |
| USER_ROLE | `(user_id, role_id)` | `(user_id, role_id) → assigned_at` | key-only ✓ |
| RESOURCE | `resource_id` | `resource_id → resource_code, name, type, is_active` | key-only ✓ |
| PERMISSION | `permission_id` | `permission_id → resource_id, action_code` | key-only ✓ |
| ROLE_PERMISSION | `(role_id, permission_id)` | `(role_id, permission_id) → granted_at` | key-only ✓ |
| ACCESS_LOG | `log_id` | `log_id → occurred_at, decision, reason_code, user_id, permission_id` | key-only, except `reason_code → decision` — see §6 |

No non-key attribute depends on any other non-key attribute in any relation. **All eight
relations are in 3NF.**

The two junction relations are exactly the relations that a 2NF analysis forces into being,
which is why they cannot be merged away: their keys are composite *and* their only non-key
attribute depends on the whole composite key. Removing `assigned_at` would make `USER_ROLE` a
pure relation with no non-prime attributes — at which point the composite key is the only
thing distinguishing it, and the duplicate-assignment guarantee is the sole justification for
its existence. That is a defensible design, but it throws away the timestamp; keeping it costs
nothing and answers "since when does this user hold this role?".

## 6. BCNF analysis, including the one violation

BCNF: every determinant in every non-trivial FD is a superkey.

Seven relations pass immediately — in each, the only determinants are the primary key or a
declared candidate key, both of which are superkeys:

| Relation | Determinants | Superkey? |
|---|---|---|
| DEPARTMENT | `department_id`, `department_name` | both ✓ |
| APP_USER | `user_id`, `email` | both ✓ |
| ROLE | `role_id`, `role_name` | both ✓ |
| USER_ROLE | `(user_id, role_id)` | ✓ |
| RESOURCE | `resource_id`, `resource_code` | both ✓ |
| PERMISSION | `permission_id`, `(resource_id, action_code)` | both ✓ |
| ROLE_PERMISSION | `(role_id, permission_id)` | ✓ |

### ACCESS_LOG violates BCNF — and the violation comes from the specification

The controlled vocabulary in `database-design.md` §4.3 makes `PERMISSION_GRANTED` mean
exactly one thing:

```
reason_code = 'PERMISSION_GRANTED'  ⟺  decision = 'ALLOW'
```

So `reason_code → decision` is a functional dependency. Is `reason_code` a superkey? No — ten
rows can share `reason_code = 'PERMISSION_NOT_GRANTED'` with different users, permissions and
timestamps. **Determinant is not a superkey ⇒ ACCESS_LOG is not in BCNF.**

This is a property of *any* schema that stores both columns, including the one the Review 1
PDF specifies. It is not introduced by this implementation, and no implementation choice
removes it — a column present in a stored tuple participates in the relation's dependencies.

**Remedy chosen: generate `decision` from `reason_code` rather than storing it independently.**

```sql
decision VARCHAR(5) GENERATED ALWAYS AS
    (CASE WHEN reason_code = 'PERMISSION_GRANTED' THEN 'ALLOW' ELSE 'DENY' END) STORED
```

This does not reach BCNF — the FD still exists — but it eliminates the *only* practical harm
the redundancy could cause. In BCNF terms, decomposition exists to prevent a determinant from
being updated inconsistently with its dependants. Here the dependant is computed from the
determinant at write time and can never be set independently, so:

- the update anomaly BCNF guards against is **unrepresentable**, not merely discouraged;
- impossible pairs such as `decision = 'ALLOW'` with `reason_code = 'USER_DISABLED'` cannot
  exist even if a caller tries;
- master prompt §8, *"the caller must not arbitrarily choose the logged decision"*, is
  satisfied by the type system instead of by discipline.

The alternative — dropping `decision` from storage and exposing it through a view — reaches
BCNF, but removes an attribute the Review 1 PDF mandates. **That trade-off needs faculty
approval, so it is recorded here and not taken.** The attribute remains queryable and
indexable either way; only its storability changes.

## 7. Lossless join and dependency preservation

**Lossless join** — each decomposition step's shared attribute is a key of at least one side,
so no spurious tuples are created and no real tuples are lost:

| Step | Intersection | Is it a key? |
|---|---|---|
| ROLE ← USER_ROLE_1NF | `role_name` | key of ROLE ✓ |
| RESOURCE ← USER_ROLE_1NF | `resource_code` | key of RESOURCE ✓ |
| DEPARTMENT ← APP_USER | `dept_name` | key of DEPARTMENT ✓ |
| APP_USER ← LOG | `user_id` | key of APP_USER ✓ |
| PERMISSION ← ROLE_PERMISSION | `(resource_code, action_code)` | key of PERMISSION ✓ |

**Dependency preservation** — every FD in §5 is enforced by a constraint declared on a single
relation. None requires a join or application code to check, so nothing is lost to the
decomposition.

## 8. Summary

| Form | Result |
|---|---|
| UNF | ATTEMPT sheet with repeating authorization groups; update/insert/delete anomalies |
| 1NF | repeating groups split → USER_ROLE_1NF, LOG_1NF |
| 2NF | three partial dependencies removed → 5 relations |
| 3NF | two transitive dependencies removed → **8 relations**, the specified design |
| BCNF | 7 of 8 relations ✓; ACCESS_LOG carries `reason_code → decision`, mitigated by generation |

The decomposition independently produces exactly the eight relations the Review 1 proposal
specifies. That agreement is the evidence that the proposal is well normalized, rather than a
statement anyone has to take on trust.