export interface Page<T> { items: T[]; total: number; limit: number; offset: number }
export interface Department { department_id: number; department_name: string }
export interface User { user_id: number; department_id: number; department_name: string; full_name: string; email: string; status: 'ACTIVE'|'DISABLED' }
export interface Role { role_id: number; role_name: string; is_active: boolean }
export interface Resource { resource_id: number; resource_code: string; name: string; type: string; is_active: boolean }
export interface Permission { permission_id: number; resource_id: number; resource_code: string; resource_name: string; action_code: string }
export interface Evaluation { decision: 'ALLOW'|'DENY'; reason_code: string; log_id: number|null; occurred_at: string|null }
export interface Audit extends Evaluation { log_id: number; occurred_at: string; full_name: string; email: string; department_name: string; resource_code: string; resource_name: string; action_code: string; user_id: number; resource_id: number; permission_id: number }
export interface DashboardStats { total_users: number; active_roles: number; total_resources: number; total_events: number; allow_count: number; deny_count: number }
export interface ResourceStats { resource_id: number; resource_code: string; resource_name: string; attempts: number; denied: number }
