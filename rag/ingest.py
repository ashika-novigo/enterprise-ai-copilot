# rag/ingest.py
# Uses HuggingFace embeddings — no Gemini, no API key needed for embeddings
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
load_dotenv()

DOCUMENTS_PATH = 'rag/documents/'
CHROMA_PATH    = 'rag/chroma_db/'

DOCUMENT_ACCESS = {
    'employee_handbook.pdf':                            ['employee', 'manager', 'hr', 'admin'],
    'Novigo Leave Policy.pdf':                          ['employee', 'manager', 'hr', 'admin'],
    'salary.pdf':                                       ['hr', 'finance', 'admin', 'manager'],
    'POSH 1.4.pdf':                                     ['employee', 'manager', 'hr', 'admin'],
    'Policy for Employees on Business Visas in KSA.pdf': ['employee', 'manager', 'hr', 'admin'],
    'code.pdf':                                         ['employee', 'manager', 'it', 'admin'],
}

def ingest_documents():
    print('Starting document ingestion...')
    all_docs = []

    for filename, allowed_roles in DOCUMENT_ACCESS.items():
        filepath = os.path.join(DOCUMENTS_PATH, filename)
        if not os.path.exists(filepath):
            print(f'  Skipping {filename} — not found')
            continue
        loader = PyPDFLoader(filepath) if filename.endswith('.pdf') else Docx2txtLoader(filepath)
        loaded = loader.load()
        for doc in loaded:
            doc.metadata['source']        = filename
            doc.metadata['allowed_roles'] = ','.join(allowed_roles)
        all_docs.extend(loaded)
        print(f'  Loaded: {filename} ({len(loaded)} pages)')

    if not all_docs:
        print('No documents found. Put PDF/DOCX files in rag/documents/')
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks   = splitter.split_documents(all_docs)
    print(f'  Split into {len(chunks)} chunks')

    # HuggingFace embeddings — runs locally, zero API cost
    embeddings = HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-MiniLM-L6-v2'
    )
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
    )
    print(f'Done! ChromaDB stored at: {CHROMA_PATH}')

if __name__ == '__main__':
    ingest_documents()