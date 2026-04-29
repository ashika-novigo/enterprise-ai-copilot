# mcp/mcp_server.py
from fastmcp import FastMCP
from db.database import SessionLocal
from db import crud
 
mcp = FastMCP('Enterprise Copilot Tools')
 
@mcp.tool()
def apply_leave(employee_id: int, leave_type: str,
                 start_date: str, end_date: str, reason: str) -> dict:
    """Apply for employee leave — stored in SQLite."""
    db = SessionLocal()
    try:
        from datetime import datetime
        start    = datetime.strptime(start_date, '%Y-%m-%d')
        end      = datetime.strptime(end_date,   '%Y-%m-%d')
        num_days = (end - start).days + 1
        req = crud.create_leave_request(db, employee_id, leave_type, start, end, num_days, reason)
        return {'status': 'success', 'leave_id': req.id, 'days': num_days}
    finally:
        db.close()
 
@mcp.tool()
def get_leave_balance(employee_id: int) -> dict:
    db = SessionLocal()
    try:
        bal = crud.get_leave_balance(db, employee_id)
        if not bal: return {'error': 'Not found'}
        return {
            'casual': bal.casual_total - bal.casual_used,
            'sick':   bal.sick_total   - bal.sick_used,
            'earned': bal.earned_total  - bal.earned_used,
        }
    finally:
        db.close()
 
if __name__ == '__main__':
    mcp.run(host='127.0.0.1', port=8000)
