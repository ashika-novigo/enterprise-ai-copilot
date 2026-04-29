# agents/approval_agent.py
from db.database import SessionLocal
from db import crud

def approve_leave(leave_id: int, approved_by: int, approve: bool) -> str:
    """Approve or reject a leave request."""
    db = SessionLocal()
    try:
        status = 'approved' if approve else 'rejected'
        req = crud.update_leave_status(db, leave_id, status, approved_by)
        if not req:
            return f'Leave request #{leave_id} not found.'
        return f'Leave request #{leave_id} has been {status}.'
    finally:
        db.close()

def get_pending_leaves(manager_id: int) -> list:
    """Get all pending leave requests for a manager to review."""
    db = SessionLocal()
    try:
        from db.models import LeaveRequest, User
        records = db.query(LeaveRequest).filter(
            LeaveRequest.status == 'pending'
        ).all()
        return [
            {
                'id':         r.id,
                'employee_id': r.employee_id,
                'leave_type':  r.leave_type,
                'start_date':  str(r.start_date.date()),
                'end_date':    str(r.end_date.date()),
                'num_days':    r.num_days,
                'reason':      r.reason,
            }
            for r in records
        ]
    finally:
        db.close()