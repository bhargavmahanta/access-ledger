# Functional dependencies and normalization

The pasted master requirements govern this analysis. The original Review 1 PDF is unavailable; no claim about its exact wording is independently verified.

## Candidate keys and dependencies

| Relation | Candidate keys | Functional dependencies |
|---|---|---|
| DEPARTMENT | department_id; department_name | Each candidate key determines all attributes. |
| APP_USER | user_id; normalized email | Each candidate key determines department_id, full_name, email, status and user_id. |
| ROLE | role_id; role_name | Each candidate key determines the remaining attributes. |
| USER_ROLE | (user_id, role_id) | The complete pair determines assigned_at. |
| RESOURCE | resource_id; resource_code | Each candidate key determines name, type, is_active and the remaining identifier. |
| PERMISSION | permission_id; (resource_id, action_code) | Each candidate key determines all attributes. |
| ROLE_PERMISSION | (role_id, permission_id) | The complete pair determines granted_at. |
| ACCESS_LOG | log_id | log_id determines user_id, permission_id, occurred_at, reason_code, decision; additionally reason_code determines decision. |

These dependencies describe the stated business rules, rather than coincidences in the small seed dataset. Candidate keys are enforced by PRIMARY KEY or UNIQUE plus NOT NULL. There is no uniqueness assumption on names, timestamps or a user/permission/time combination.

## 1NF and 2NF

All columns hold scalar values; roles and permissions are rows in junction relations, never comma-separated lists. All eight relations satisfy 1NF. USER_ROLE and ROLE_PERMISSION have composite keys and only one non-key attribute, respectively assigned_at and granted_at, depending on the entire pair. The remaining relations have single-column candidate keys (PERMISSION also has a resource/action candidate key); no non-prime attribute depends on a proper subset of a candidate key. All eight satisfy 2NF.

## 3NF and BCNF

For a nontrivial FD X → A, 3NF requires X to be a superkey or A to be prime. BCNF requires X to be a superkey. The first seven relations satisfy both under the dependencies above.

ACCESS_LOG does **not** satisfy 3NF or BCNF: reason_code → decision, reason_code is not a superkey, and decision is not prime. Previous documentation incorrectly claimed this only violated BCNF. A generated stored column still participates in the relation's functional dependencies.

The specified eight-table model requires both decision and reason_code. Retain this deliberate redundancy and generate decision from reason_code, preventing inconsistent pairs. Do not claim the generated column removes the normalization violation. A hypothetical design could remove stored decision and derive it in a view; that is not the requested stored schema.

## Why two junctions

User-to-role and role-to-permission are separate many-to-many facts. A combined user/role/permission table would repeat assignment timestamps for every role permission and grant timestamps for every user holding the role, creating partial dependencies and update anomalies. Separate junctions enforce unique pairs and allow revocation independently of the permission definition.

## Referential integrity and historical meaning

Every FK is required and uses ON DELETE RESTRICT. A logged permission cannot change its resource/action identity. Role revocation deletes current assignments but preserves past decisions. Audit joins display current user/department/resource labels; the eight-table model does not snapshot historical labels or store policy-change history. No proof of a larger universal-relation decomposition is asserted without an explicit universal relation and its complete dependencies.
