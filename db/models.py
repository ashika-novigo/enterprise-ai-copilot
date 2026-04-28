# db/models.py
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum, Boolean, ForeignKey
from datetime import datetime
from .database import Base
import enum
 
class UserRole(str, enum.Enum):
    employee = 'employee'
    manager  = 'manager'
    hr       = 'hr'
    it       = 'it'
    finance  = 'finance'
    admin    = 'admin'
 
class LeaveStatus(str, enum.Enum):
    pending   = 'pending'
    approved  = 'approved'
    rejected  = 'rejected'
    cancelled = 'cancelled'
 
class TicketStatus(str, enum.Enum):
    open        = 'open'
    in_progress = 'in_progress'
    resolved    = 'resolved'
    closed      = 'closed'
 
# ── Users Table ───────────────────────────────────
class User(Base):
    __tablename__ = 'users'
    id          = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True)  # e.g. EMP001
    name        = Column(String, nullable=False)
    email       = Column(String, unique=True, index=True)
    department  = Column(String)
    role        = Column(String, default=UserRole.employee.value)
    manager_id  = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
 
# ── Leave Requests Table ──────────────────────────
class LeaveRequest(Base):
    __tablename__ = 'leave_requests'
    id          = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('users.id'))
    leave_type  = Column(String)   # casual / sick / earned / maternity
    start_date  = Column(DateTime)
    end_date    = Column(DateTime)
    num_days    = Column(Integer)
    reason      = Column(Text)
    status      = Column(String, default=LeaveStatus.pending.value)
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow)
 
# ── Leave Balance Table ───────────────────────────
class LeaveBalance(Base):
    __tablename__ = 'leave_balances'
    id           = Column(Integer, primary_key=True)
    employee_id  = Column(Integer, ForeignKey('users.id'), unique=True)
    casual_total = Column(Integer, default=12)
    casual_used  = Column(Integer, default=0)
    sick_total   = Column(Integer, default=10)
    sick_used    = Column(Integer, default=0)
    earned_total = Column(Integer, default=21)
    earned_used  = Column(Integer, default=0)
    year         = Column(Integer, default=2025)
 
# ── IT Tickets Table ──────────────────────────────
class ITTicket(Base):
    __tablename__ = 'it_tickets'
    id          = Column(Integer, primary_key=True, index=True)
    ticket_id   = Column(String, unique=True)   # e.g. TKT-2025-001
    employee_id = Column(Integer, ForeignKey('users.id'))
    issue_type  = Column(String)   # laptop / vpn / email / printer
    description = Column(Text)
    priority    = Column(String, default='medium')  # low / medium / high
    status      = Column(String, default=TicketStatus.open.value)
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolution  = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
 
# ── Asset Requests Table ──────────────────────────
class AssetRequest(Base):
    __tablename__ = 'asset_requests'
    id               = Column(Integer, primary_key=True)
    employee_id      = Column(Integer, ForeignKey('users.id'))
    asset_type       = Column(String)   # laptop / monitor / keyboard
    justification    = Column(Text)
    manager_approved = Column(Boolean, nullable=True)
    it_approved      = Column(Boolean, nullable=True)
    status           = Column(String, default='pending')
    created_at       = Column(DateTime, default=datetime.utcnow)
 
# ── Reimbursements Table ──────────────────────────
class Reimbursement(Base):
    __tablename__ = 'reimbursements'
    id          = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('users.id'))
    claim_type  = Column(String)   # travel / internet / food / client
    amount      = Column(Float)
    description = Column(Text)
    receipt_path = Column(String, nullable=True)
    status      = Column(String, default='pending')
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
