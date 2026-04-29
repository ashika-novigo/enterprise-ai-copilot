# middleware/rbac.py
 
ROLE_PERMISSIONS = {
    'employee': [
        'view_own_tickets', 'create_ticket',
        'apply_leave', 'check_own_leave_balance', 'view_own_leave_history',
        'ask_hr_policy', 'view_own_payslip', 'submit_reimbursement'
    ],
    'manager': [
        '__inherit__employee',
        'approve_leave', 'view_team_leaves', 'approve_asset_request'
    ],
    'hr': [
        '__inherit__manager',
        'view_all_leaves', 'view_salary_docs', 'access_hr_reports'
    ],
    'it': [
        '__inherit__employee',
        'view_all_tickets', 'assign_ticket', 'resolve_ticket', 'view_inventory'
    ],
    'finance': [
        '__inherit__employee',
        'view_all_payslips', 'approve_reimbursement', 'view_salary_reports'
    ],
    'admin': ['*'],
}
 
def get_permissions(role: str) -> set:
    perms = set()
    for p in ROLE_PERMISSIONS.get(role, []):
        if p.startswith('__inherit__'):
            perms |= get_permissions(p.replace('__inherit__', ''))
        else:
            perms.add(p)
    return perms
 
def has_permission(role: str, permission: str) -> bool:
    if role == 'admin': return True
    return permission in get_permissions(role)
 
def require_permission(role: str, permission: str):
    if not has_permission(role, permission):
        raise PermissionError(f'Role {role!r} lacks permission: {permission}')
