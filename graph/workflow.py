# graph/workflow.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import AgentState
from agents.router_agent import detect_intent
from agents.hr_agent import run_hr_agent
from agents.it_agent import run_it_agent
from agents.finance_agent import run_finance_agent
from middleware.rbac import has_permission

def node_detect_intent(state: AgentState) -> AgentState:
    return {**state, 'intent': detect_intent(state['query'])}

def node_validate_rbac(state: AgentState) -> AgentState:
    perm_map = {
        'HR':      'apply_leave',
        'IT':      'create_ticket',
        'FINANCE': 'view_own_payslip',
    }
    required = perm_map.get(state['intent'], 'ask_hr_policy')
    if not has_permission(state['user_role'], required):
        return {**state, 'error': f'Access denied for {state["intent"]} operations.'}
    return state

def node_hr_agent(state: AgentState) -> AgentState:
    response = run_hr_agent(
        state['query'], state['employee_id'],
        state['user_role'], state.get('chat_history', [])
    )
    needs = ('leave' in state['query'].lower() and
             'apply' in state['query'].lower())
    return {**state, 'agent_response': response, 'needs_approval': needs}

def node_it_agent(state: AgentState) -> AgentState:
    response = run_it_agent(
        state['query'], state['employee_id'],
        state['user_role'], state.get('chat_history', [])
    )
    return {**state, 'agent_response': response, 'needs_approval': False}

def node_finance_agent(state: AgentState) -> AgentState:
    response = run_finance_agent(
        state['query'], state['employee_id'],
        state['user_role'], state.get('chat_history', [])
    )
    return {**state, 'agent_response': response, 'needs_approval': False}

def node_human_approval(state: AgentState) -> AgentState:
    return {**state, 'approval_status': 'pending',
            'agent_response': state['agent_response'] + '\n\n⏳ Awaiting manager approval.'}

def node_save_memory(state: AgentState) -> AgentState:
    history = state.get('chat_history', [])
    history.append({'role': 'user',      'content': state['query']})
    history.append({'role': 'assistant', 'content': state.get('agent_response', '')})
    return {**state, 'chat_history': history[-20:]}

def node_final_response(state: AgentState) -> AgentState:
    if state.get('error'):
        return {**state, 'final_response': f'Access Denied: {state["error"]}'}
    return {**state, 'final_response': state.get('agent_response', 'Error.')}

def route_by_intent(state: AgentState) -> str:
    if state.get('error'): return 'final_response'
    return {
        'HR':      'hr_agent',
        'IT':      'it_agent',
        'FINANCE': 'finance_agent',
        'GENERAL': 'hr_agent',
    }.get(state.get('intent', 'GENERAL'), 'hr_agent')

def route_after_agent(state: AgentState) -> str:
    return 'human_approval' if state.get('needs_approval') else 'save_memory'

def build_graph():
    g = StateGraph(AgentState)
    g.add_node('detect_intent',  node_detect_intent)
    g.add_node('validate_rbac',  node_validate_rbac)
    g.add_node('hr_agent',       node_hr_agent)
    g.add_node('it_agent',       node_it_agent)
    g.add_node('finance_agent',  node_finance_agent)
    g.add_node('human_approval', node_human_approval)
    g.add_node('save_memory',    node_save_memory)
    g.add_node('final_response', node_final_response)
    g.set_entry_point('detect_intent')
    g.add_edge('detect_intent', 'validate_rbac')
    g.add_conditional_edges('validate_rbac',  route_by_intent)
    g.add_conditional_edges('hr_agent',       route_after_agent)
    g.add_conditional_edges('it_agent',       route_after_agent)
    g.add_conditional_edges('finance_agent',  route_after_agent)
    g.add_edge('human_approval', 'save_memory')
    g.add_edge('save_memory',    'final_response')
    g.add_edge('final_response', END)
    return g.compile(checkpointer=MemorySaver())

compiled_graph = build_graph()

def run_copilot(query: str, employee_id: int, user_role: str,
                 user_email: str, thread_id: str = 'default') -> str:
    config = {'configurable': {'thread_id': thread_id}}
    state  = {
        'query': query, 'employee_id': employee_id,
        'user_role': user_role, 'user_email': user_email,
        'chat_history': []
    }
    result = compiled_graph.invoke(state, config=config)
    return result.get("final_response", "No response generated")