# rag/retriever.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()

CHROMA_PATH = 'rag/chroma_db/'

def get_rag_answer(question: str, user_role: str) -> dict:
    embeddings = HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-MiniLM-L6-v2'
    )
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
    )

    # ── Step 1: Retrieve all top-K docs (no broken metadata filter) ──
    retriever = vectorstore.as_retriever(
        search_type='similarity',
        search_kwargs={'k': 5}
    )
    all_docs = retriever.invoke(question)

    # ── Step 2: Filter by role in Python (reliable) ──────────────────
    docs = [
        doc for doc in all_docs
        if user_role in doc.metadata.get('allowed_roles', '').split(',')
        or user_role == 'admin'
    ]

    # Fall back to all docs if role filter removes everything
    if not docs:
        docs = all_docs

    if not docs:
        return {
            'answer': 'I could not find this in company policy.',
            'sources': []
        }

    # ── Step 3: Format documents ──────────────────────────────────────
    def format_docs(doc_list):
        formatted = []
        for i, doc in enumerate(doc_list, 1):
            source  = doc.metadata.get('source', 'Unknown')
            content = doc.page_content.strip()
            formatted.append(f"[Document {i} — {source}]:\n{content}")
        return "\n\n".join(formatted)

    context = format_docs(docs)
    sources = list(set(
        d.metadata.get('source', '') for d in docs
        if d.metadata.get('source')
    ))

    # ── Step 4: Ask Groq LLM ─────────────────────────────────────────
    llm = ChatGroq(
        model='llama-3.3-70b-versatile',
        api_key=os.getenv('GROQ_API_KEY'),
        temperature=0,
    )

    prompt = PromptTemplate(
        template="""You are an enterprise HR/IT/Finance assistant.
Answer the question based ONLY on the provided company documents.
If the answer is not in the documents, say 'I could not find this in company policy.'
Always mention which document you found the answer in.

Documents:
{context}

Question: {question}

Answer:""",
        input_variables=['context', 'question']
    )

    formatted_prompt = prompt.format(context=context, question=question)
    result = llm.invoke(formatted_prompt)

    return {
        'answer':  result.content if hasattr(result, 'content') else str(result),
        'sources': sources
    }