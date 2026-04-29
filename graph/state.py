# graph/state.py
from typing import TypedDict, Optional, List
 
class AgentState(TypedDict):
    query:           str
    employee_id:     int
    user_role:       str
    user_email:      str
    intent:          Optional[str]
    agent_response:  Optional[str]
    needs_approval:  Optional[bool]
    approval_status: Optional[str]
    chat_history:    List[dict]
    final_response:  Optional[str]
    error:           Optional[str]
