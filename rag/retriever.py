# rag/retriever.py
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate   
import os
from dotenv import load_dotenv
 
load_dotenv()
 
CHROMA_PATH = 'rag/chroma_db/'
 
RAG_PROMPT =PromptTemplate(
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
 
def get_rag_answer(question: str, user_role: str) -> dict:
    # Use Gemini embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model='models/embedding-001',
        google_api_key=os.getenv('GOOGLE_API_KEY'),
    )
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
    )
 
    # Role-filtered retrieval
    retriever = vectorstore.as_retriever(
        search_type='similarity',
        search_kwargs={
            'k': 5,
            'filter': {'allowed_roles': {'$contains': user_role}},
        }
    )
 
    # Use Gemini 1.5 Pro for answering
    llm = ChatGoogleGenerativeAI(
           model=os.getenv('MODEL_NAME'),
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        temperature=0,
    )
 
  # NEW — modern LCEL chain, replaces RetrievalQA completely:
    def format_docs(docs):
     return "\n\n".join(doc.page_content for doc in docs)

    chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | RAG_PROMPT
    | llm
    | StrOutputParser()
    )

    docs    = retriever.invoke(question)
    sources = list(set(d.metadata.get('source', '') for d in docs))
    answer  = chain.invoke(question)

    return {'answer': answer, 'sources': sources}