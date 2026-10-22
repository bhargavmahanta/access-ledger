# Relational schema

Underlined keys are expressed here as PK(...); UK means an additional candidate key.

```text
DEPARTMENT(department_id, department_name)
 PK(department_id), UK(department_name)
APP_USER(user_id, department_id, full_name, email, status)
 PK(user_id), UK(email), FK(department_id) → DEPARTMENT
ROLE(role_id, role_name, is_active)
 PK(role_id), UK(role_name)
USER_ROLE(user_id, role_id, assigned_at)
 PK(user_id, role_id), FK(user_id) → APP_USER, FK(role_id) → ROLE
RESOURCE(resource_id, resource_code, name, type, is_active)
 PK(resource_id), UK(resource_code)
PERMISSION(permission_id, resource_id, action_code)
 PK(permission_id), UK(resource_id, action_code), FK(resource_id) → RESOURCE
ROLE_PERMISSION(role_id, permission_id, granted_at)
 PK(role_id, permission_id), FK(role_id) → ROLE, FK(permission_id) → PERMISSION
ACCESS_LOG(log_id, user_id, permission_id, occurred_at, decision, reason_code)
 PK(log_id), FK(user_id) → APP_USER, FK(permission_id) → PERMISSION
```

All FKs are NOT NULL and ON DELETE RESTRICT. Identity columns supply single-column PKs; timestamp defaults apply to assignments/grants/events. Decision is stored generated and NOT NULL. Status/reason CHECKs and boolean defaults are in the authoritative SQL. Email is normalized before its unique constraint is checked. See database-design.md for sizes and policy rules, normalization.md for FD analysis, and er-diagram.svg for the exported Crow's Foot model.
