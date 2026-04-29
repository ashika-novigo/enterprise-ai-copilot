# agents/router_agent.py
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()

ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ('system', '''Classify the user query into one department.
    Reply with ONLY one word — nothing else.
    Departments: HR, IT, FINANCE, GENERAL

    HR: leave, vacation, policy, WFH, maternity, notice period, sick leave
    IT: laptop, VPN, email issues, printer, software, network, ticket
    FINANCE: payslip, salary, reimbursement, tax, PF, claims
    GENERAL: anything else'''),
    ('human', '{query}')
])

def detect_intent(query: str) -> str:
    llm = ChatGroq(
        model='llama-3.1-8b-instant',       # fastest model — good for routing
        api_key=os.getenv('GROQ_API_KEY'),
        temperature=0,
    )
    result = (ROUTER_PROMPT | llm).invoke({'query': query})
    intent = result.content.strip().upper()
    return intent if intent in ['HR', 'IT', 'FINANCE', 'GENERAL'] else 'GENERAL'