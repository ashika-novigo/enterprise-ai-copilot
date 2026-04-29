# agents/finance_agent.py
from langchain_groq import ChatGroq
from langchain_classic.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from db.database import SessionLocal
from db import crud
from rag.retriever import get_rag_answer
import os
from dotenv import load_dotenv
load_dotenv()

@tool
def answer_finance_policy(question: str, user_role: str = 'employee') -> str:
    """Answer finance policy questions from company documents."""
    try:
        result = get_rag_answer(question, user_role)
        answer = result.get('answer', 'No answer found').strip()
        sources = result.get('sources', [])
        sources = [s for s in sources if s]  # filter empty strings
        source_text = f"\n\nSources: {', '.join(sources)}" if sources else ""
        if not answer or 'could not find' in answer.lower():
            return f"I could not find this information in finance policies. Please contact Finance support."
        return f"{answer}{source_text}"
    except Exception as e:
        return f"Error retrieving policy information: {str(e)}. Please contact Finance support."

@tool
def get_my_reimbursements(employee_id: int) -> str:
    """Get all reimbursement claims for an employee."""
    db = SessionLocal()
    try:
        records = crud.get_my_reimbursements(db, employee_id)
        if not records:
            return 'No reimbursement claims found.'
        lines = ['Your Reimbursements:']
        for r in records:
            lines.append(f'  #{r.id} | {r.claim_type} | ₹{r.amount} | {r.status}')
        return '\n'.join(lines)
    finally:
        db.close()

@tool
def submit_reimbursement(employee_id: int, claim_type: str,
                          amount: float, description: str) -> str:
    """Submit a reimbursement claim. claim_type: travel/internet/food/client."""
    db = SessionLocal()
    try:
        claim = crud.create_reimbursement(db, employee_id, claim_type, amount, description)
        return f'Reimbursement claim #{claim.id} submitted for ₹{amount}. Status: PENDING'
    finally:
        db.close()

FINANCE_SYSTEM_PROMPT = """You are the Finance Assistant.
Help employees with:
- Reimbursement claims (travel, internet, food, client expenses)
- Checking claim status
- Finance policy questions

Always confirm claim details before submitting."""

finance_tools = [get_my_reimbursements, submit_reimbursement, answer_finance_policy]

def run_finance_agent(query: str, employee_id: int, user_role: str,
                       chat_history: list = []) -> str:
    llm = ChatGroq(
        model='llama-3.3-70b-versatile',    # strong model for finance calculations
        api_key=os.getenv('GROQ_API_KEY'),
        temperature=0,
    )
    
    # Bind employee_id to tools so LLM doesn't need to extract it
    @tool
    def my_reimbursements() -> str:
        """Get all my reimbursement claims."""
        return get_my_reimbursements(employee_id)
    
    @tool
    def submit_claim(claim_type: str, amount: float, description: str) -> str:
        """Submit a reimbursement claim. Types: travel/internet/food/client."""
        return submit_reimbursement(employee_id, claim_type, amount, description)
    
    # Use bound tools
    bound_tools = [my_reimbursements, submit_claim, answer_finance_policy]
    
    prompt = ChatPromptTemplate.from_messages([
        ('system', FINANCE_SYSTEM_PROMPT),
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
        output = "I couldn't generate a response. Please try rephrasing your question or contact Finance support."
    return output