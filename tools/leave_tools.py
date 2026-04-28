# tools/leave_tools.py
from langchain.tools import tool
from db.database import SessionLocal
from db import crud, models
from datetime import datetime
 
@tool
def check_leave_balance(employee_id: int) -> str:
    """Check leave balance for an employee. Returns remaining days by type."""
    db = SessionLocal()
    try:
        balance = crud.get_leave_balance(db, employee_id)
        if not balance:
            return 'No leave balance record found.'
        return (
            f'Leave Balance for Employee {employee_id}:\n'
            f'  Casual Leave: {balance.casual_total - balance.casual_used} days remaining\n'
            f'  Sick Leave:   {balance.sick_total - balance.sick_used} days remaining\n'
            f'  Earned Leave: {balance.earned_total - balance.earned_used} days remaining'
        )
    finally:
        db.close()
 
@tool
def apply_leave(employee_id: int, leave_type: str, start_date: str,
                 end_date: str, reason: str) -> str:
    """Apply for leave. Dates must be in YYYY-MM-DD format."""
    db = SessionLocal()
    try:
        start    = datetime.strptime(start_date, '%Y-%m-%d')
        end      = datetime.strptime(end_date,   '%Y-%m-%d')
        num_days = (end - start).days + 1
 
        if num_days <= 0:
            return 'Error: End date must be after start date.'
 
        # Check for overlapping leaves in SQLite
        existing = db.query(models.LeaveRequest).filter(
            models.LeaveRequest.employee_id == employee_id,
            models.LeaveRequest.status.in_(['pending', 'approved']),
            models.LeaveRequest.start_date <= end,
            models.LeaveRequest.end_date   >= start,
        ).first()
 
        if existing:
            return 'Error: You already have a leave request overlapping these dates.'
 
        req = crud.create_leave_request(db, employee_id, leave_type, start, end, num_days, reason)
        return f'Leave request #{req.id} submitted for {num_days} days. Status: PENDING'
    finally:
        db.close()
 
@tool
def get_leave_history(employee_id: int) -> str:
    """Get leave history for an employee from SQLite."""
    db = SessionLocal()
    try:
        records = db.query(models.LeaveRequest).filter(
            models.LeaveRequest.employee_id == employee_id
        ).order_by(models.LeaveRequest.created_at.desc()).limit(10).all()
        if not records:
            return 'No leave history found.'
        lines = ['Recent Leave Requests:']
        for r in records:
            lines.append(f'  #{r.id} | {r.leave_type} | {r.start_date.date()} to {r.end_date.date()} | {r.status}')
        return '\n'.join(lines)
    finally:
        db.close()
