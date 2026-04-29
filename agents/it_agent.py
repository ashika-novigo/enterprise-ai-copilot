# agents/it_agent.py
from langchain_groq import ChatGroq
from langchain_classic.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools.ticket_tools import create_it_ticket, get_my_tickets, update_ticket
from tools.email_tools import send_email
from tools.search_tools import web_search
from rag.retriever import get_rag_answer
from langchain_core.tools import tool
import os
from dotenv import load_dotenv
load_dotenv()

@tool
def answer_office_policy(question: str, user_role: str = 'employee') -> str:
    """Answer office, facility, and workplace policy questions from company documents."""
    try:
        result = get_rag_answer(question, user_role)
        answer = result.get('answer', 'No answer found').strip()
        sources = result.get('sources', [])
        sources = [s for s in sources if s]  # filter empty strings
        source_text = f"\n\nSources: {', '.join(sources)}" if sources else ""
        if not answer or 'could not find' in answer.lower():
            return f"I could not find this information in office policies. Please contact IT support."
        return f"{answer}{source_text}"
    except Exception as e:
        return f"Error retrieving policy information: {str(e)}. Please contact IT support."

IT_SYSTEM_PROMPT = """You are the IT Support Assistant for the enterprise.
Help employees with:
- Technical issues: laptop, VPN, email, printer, network, software
- Office facilities and workplace policies (using office policy tool)
- Create and manage IT support tickets
- Provide troubleshooting steps

Before creating a ticket:
1. Ask for more details about the issue
2. Provide basic troubleshooting steps
3. Only create a ticket if the issue persists

For policy questions about office location, facilities, or workplace rules, use the answer_office_policy tool.
Always be helpful and provide ticket IDs after creation."""

it_tools = [create_it_ticket, get_my_tickets, update_ticket,
            send_email, web_search, answer_office_policy]

def run_it_agent(query: str, employee_id: int, user_role: str,
                  chat_history: list = []) -> str:
    llm = ChatGroq(
        model='llama-3.1-8b-instant',       # fast model for IT support
        api_key=os.getenv('GROQ_API_KEY'),
        temperature=0,
    )
    
    # Bind employee_id to tools so LLM doesn't need to extract it
    @tool
    def create_ticket(issue_type: str, description: str, priority: str = 'medium') -> str:
        """Create an IT support ticket. Priority: low/medium/high."""
        return create_it_ticket(employee_id, issue_type, description, priority)
    
    @tool
    def my_tickets() -> str:
        """Get my IT support tickets."""
        return get_my_tickets(employee_id)
    
    # Use bound tools
    bound_tools = [create_ticket, my_tickets, update_ticket,
                   send_email, web_search, answer_office_policy]
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', IT_SYSTEM_PROMPT),
        MessagesPlaceholder('chat_history', optional=True),
        ('human', '{input}'),
        MessagesPlaceholder('agent_scratchpad'),
    ])
    agent    = create_openai_functions_agent(llm, bound_tools, prompt)
    executor = AgentExecutor(agent=agent, tools=bound_tools, verbose=True, 
                            handle_parsing_errors=True, return_intermediate_steps=False)
    enriched = f'Employee {employee_id} ({user_role}): {query}'
    result   = executor.invoke({'input': enriched, 'chat_history': chat_history})
    output = result.get('output', '').strip()
    if not output:
        output = "I couldn't generate a response. Please try again or contact IT support."
    return output