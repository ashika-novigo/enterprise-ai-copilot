# agents/hr_agent.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain.tools import tool
from tools.leave_tools import check_leave_balance, apply_leave, get_leave_history
from tools.email_tools import send_email
from rag.retriever import get_rag_answer
import os


 
@tool
def answer_hr_policy(question: str, user_role: str = 'employee') -> str:
    """Answer questions about HR policies from company documents."""
    result = get_rag_answer(question, user_role)
    return f"{result['answer']}\n\nSources: {', '.join(result['sources'])}"
 
HR_SYSTEM_PROMPT = """You are the HR Assistant for the enterprise.
You help employees with:
- HR policy questions (notice period, leave rules, WFH policy, maternity leave)
- Leave applications, balance checks, and leave history
 
Always be polite and professional.
When applying leave, confirm details before submitting.
For leave > 5 days, inform that manager approval will be required."""
 
hr_tools = [answer_hr_policy, check_leave_balance, apply_leave, get_leave_history, send_email]
 
def run_hr_agent(query: str, employee_id: int, user_role: str,
                  chat_history: list = []) -> str:
    # Use Gemini 1.5 Pro for HR (strong model for nuanced policy Q&A)
    llm = ChatGoogleGenerativeAI(
        model=os.getenv('MODEL_NAME'),
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        temperature=0,
    )
    prompt = ChatPromptTemplate.from_messages([
        ('system', HR_SYSTEM_PROMPT),
        MessagesPlaceholder('chat_history', optional=True),
        ('human', '{input}'),
        MessagesPlaceholder('agent_scratchpad'),
    ])
    agent    = create_openai_functions_agent(llm, hr_tools, prompt)
    executor = AgentExecutor(agent=agent, tools=hr_tools, verbose=True)
    enriched = f'[Employee ID: {employee_id}, Role: {user_role}] {query}'
    result   = executor.invoke({'input': enriched, 'chat_history': chat_history})
    return result['output']
