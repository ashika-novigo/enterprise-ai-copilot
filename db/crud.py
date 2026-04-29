# db/crud.py
from sqlalchemy.orm import Session
from db.models import LeaveRequest, LeaveBalance, ITTicket, AssetRequest, Reimbursement
from datetime import datetime

# ── Leave ──────────────────────────────────────────────
def get_leave_balance(db: Session, employee_id: int):
    return db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id
    ).first()

def check_overlapping_leave(db: Session, employee_id: int, start_date, end_date):
    return db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status.in_(['pending', 'approved']),
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date   >= start_date,
    ).first()

def create_leave_request(db: Session, employee_id: int, leave_type: str,
                          start_date, end_date, num_days: int, reason: str):
    req = LeaveRequest(
        employee_id=employee_id, leave_type=leave_type,
        start_date=start_date, end_date=end_date,
        num_days=num_days, reason=reason,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

def get_leave_history(db: Session, employee_id: int):
    return db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id
    ).order_by(LeaveRequest.created_at.desc()).limit(10).all()

def update_leave_status(db: Session, leave_id: int, status: str, approved_by: int = None):
    req = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if req:
        req.status = status
        req.approved_by = approved_by
        req.updated_at = datetime.utcnow()
        db.commit()
    return req

# ── Tickets ────────────────────────────────────────────
def check_duplicate_ticket(db: Session, employee_id: int, issue_type: str):
    return db.query(ITTicket).filter(
        ITTicket.employee_id == employee_id,
        ITTicket.issue_type  == issue_type,
        ITTicket.status      == 'open',
    ).first()

def create_ticket(db: Session, employee_id: int, issue_type: str,
                   description: str, priority: str = 'medium'):
    count     = db.query(ITTicket).count()
    ticket_id = f'TKT-{datetime.now().year}-{count+1:03d}'
    ticket = ITTicket(
        ticket_id=ticket_id, employee_id=employee_id,
        issue_type=issue_type, description=description, priority=priority,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

def get_employee_tickets(db: Session, employee_id: int):
    return db.query(ITTicket).filter(
        ITTicket.employee_id == employee_id
    ).order_by(ITTicket.created_at.desc()).all()

def get_all_tickets(db: Session):
    return db.query(ITTicket).order_by(ITTicket.created_at.desc()).all()

def update_ticket_status(db: Session, ticket_id: str, status: str, resolution: str = None):
    ticket = db.query(ITTicket).filter(ITTicket.ticket_id == ticket_id).first()
    if ticket:
        ticket.status = status
        ticket.resolution = resolution
        if status == 'resolved':
            ticket.resolved_at = datetime.utcnow()
        db.commit()
    return ticket

# ── Reimbursements ─────────────────────────────────────
def create_reimbursement(db: Session, employee_id: int, claim_type: str,
                          amount: float, description: str):
    claim = Reimbursement(
        employee_id=employee_id, claim_type=claim_type,
        amount=amount, description=description,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim

def get_my_reimbursements(db: Session, employee_id: int):
    return db.query(Reimbursement).filter(
        Reimbursement.employee_id == employee_id
    ).order_by(Reimbursement.created_at.desc()).all()