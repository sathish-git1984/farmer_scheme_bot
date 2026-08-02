# ingest.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

PDF_PATH = "./data/TN_Agriculture_FarmersWelfare_PolicyNote_2023-24.pdf"
DB_DIR = "./chroma_db"

def build_vector_store():
    print("📥 Loading PDF document...")
    loader = PyPDFLoader(PDF_PATH)
    docs = loader.load()
    print(f"Loaded {len(docs)} pages.")

    print("✂️ Chunking text...")
    # Recursive splitter works best for policy/legal documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    print("🧠 Generating embeddings and indexing in ChromaDB...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    print("✅ Vector database successfully built at:", DB_DIR)
    return vectorstore

if __name__ == "__main__":
    build_vector_store()