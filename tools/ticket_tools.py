# tools/ticket_tools.py
from langchain_core.tools import tool
from db.database import SessionLocal
from db import crud

@tool
def create_it_ticket(employee_id: int, issue_type: str,
                      description: str, priority: str = 'medium') -> str:
    """Create an IT support ticket. issue_type: laptop/vpn/email/printer/network."""
    db = SessionLocal()
    try:
        duplicate = crud.check_duplicate_ticket(db, employee_id, issue_type)
        if duplicate:
            return f'You already have an open {issue_type} ticket: {duplicate.ticket_id}'
        ticket = crud.create_ticket(db, employee_id, issue_type, description, priority)
        return f'Ticket {ticket.ticket_id} created. Priority: {priority}'
    finally:
        db.close()

@tool
def get_my_tickets(employee_id: int) -> str:
    """Get all IT tickets for an employee."""
    db = SessionLocal()
    try:
        tickets = crud.get_employee_tickets(db, employee_id)
        if not tickets:
            return 'You have no IT tickets.'
        lines = ['Your Tickets:']
        for t in tickets:
            lines.append(f'  {t.ticket_id} | {t.issue_type} | {t.status} | {t.priority}')
        return '\n'.join(lines)
    finally:
        db.close()

@tool
def update_ticket(ticket_id: str, status: str, resolution: str = '') -> str:
    """Update an IT ticket status. status: in_progress/resolved/closed."""
    db = SessionLocal()
    try:
        ticket = crud.update_ticket_status(db, ticket_id, status, resolution)
        if not ticket:
            return f'Ticket {ticket_id} not found.'
        return f'Ticket {ticket_id} updated to {status}'
    finally:
        db.close()