# agents/hr_agent.py
from langchain_groq import ChatGroq
from langchain_classic.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from tools.leave_tools import check_leave_balance, apply_leave, get_leave_history
from tools.email_tools import send_email
from rag.retriever import get_rag_answer
import os
from dotenv import load_dotenv
load_dotenv()

@tool
def answer_hr_policy(question: str, user_role: str = 'employee') -> str:
    """Answer HR policy questions from company documents."""
    try:
        result = get_rag_answer(question, user_role)
        answer = result.get('answer', 'No answer found').strip()
        sources = result.get('sources', [])
        sources = [s for s in sources if s]  # filter empty strings
        source_text = f"\n\nSources: {', '.join(sources)}" if sources else ""
        if not answer or 'could not find' in answer.lower():
            return f"I could not find this information in HR policies. Please contact HR support."
        return f"{answer}{source_text}"
    except Exception as e:
        return f"Error retrieving policy information: {str(e)}. Please contact HR support."

HR_SYSTEM_PROMPT = """You are the HR Assistant for the enterprise.
Help employees with:
- HR policy questions (notice period, leave rules, WFH, maternity leave)
- Leave applications, balance checks, and leave history

Always be polite and professional.
Confirm leave details with the employee before submitting.
For leave greater than 5 days, warn that manager approval is required."""

hr_tools = [answer_hr_policy, check_leave_balance, apply_leave,
            get_leave_history, send_email]

def run_hr_agent(query: str, employee_id: int, user_role: str,
                  chat_history: list = []) -> str:
    llm = ChatGroq(
        model='llama-3.3-70b-versatile',    # strong model for HR reasoning
        api_key=os.getenv('GROQ_API_KEY'),
        temperature=0,
    )
    
    # Bind employee_id to tools so LLM doesn't need to extract it
    @tool
    def get_leave_balance() -> str:
        """Get current leave balance (casual, sick, earned)."""
        return check_leave_balance(employee_id)
    
    @tool
    def apply_leave_request(leave_type: str, start_date: str, end_date: str, reason: str) -> str:
        """Apply for leave. Dates in YYYY-MM-DD format. Types: casual/sick/earned/maternity."""
        return apply_leave(employee_id, leave_type, start_date, end_date, reason)
    
    @tool
    def check_history() -> str:
        """Check leave request history."""
        return get_leave_history(employee_id)
    
    # Use bound tools
    bound_tools = [answer_hr_policy, get_leave_balance, apply_leave_request, 
                   check_history, send_email]
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', HR_SYSTEM_PROMPT),
        MessagesPlaceholder('chat_history', optional=True),
        ('human', '{input}'),
        MessagesPlaceholder('agent_scratchpad'),
    ])
    agent    = create_openai_functions_agent(llm, bound_tools, prompt)
    executor = AgentExecutor(
        agent=agent, 
        tools=bound_tools, 
        verbose=False,  # Turn off verbose to reduce noise
        handle_parsing_errors=True, 
        return_intermediate_steps=True,  # Get intermediate steps for debugging
        max_iterations=10
    )
    enriched = f'Employee {employee_id} ({user_role}): {query}'
    
    try:
        result = executor.invoke({'input': enriched, 'chat_history': chat_history})
        output = result.get('output', '').strip()
        
        # If no output from agent, check intermediate steps
        if not output and result.get('intermediate_steps'):
            steps = result.get('intermediate_steps', [])
            if steps:
                # Last tool result might have the answer
                last_step = steps[-1]
                if isinstance(last_step, tuple) and len(last_step) > 1:
                    output = str(last_step[1]).strip()
        
        # Last resort: try to get any useful output
        if not output:
            # Maybe the result is in a different format
            if isinstance(result, dict):
                for key in ['output', 'result', 'answer', 'response']:
                    if result.get(key):
                        output = str(result[key]).strip()
                        break
        
        if not output:
            output = "I couldn't generate a response. Please try rephrasing your question or contact HR support."
        return output
    except Exception as e:
        return f"Error: {str(e)}. Please try again or contact HR support."