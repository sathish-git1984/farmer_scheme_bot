# graph_ingest.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph

# 1. Load Environment Variables
load_dotenv()

neo4j_uri = os.getenv("NEO4J_URI")

# Auto-convert neo4j+s:// to neo4j+ssc:// if running on Windows SSL setup
if neo4j_uri and neo4j_uri.startswith("neo4j+s://"):
    neo4j_uri = neo4j_uri.replace("neo4j+s://", "neo4j+ssc://")

# 2. Connect to Neo4j AuraDB
print(f"🔌 Connecting to Neo4j AuraDB ({neo4j_uri})...")
graph = Neo4jGraph(
    url=neo4j_uri,
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# 3. Load PDF Document
PDF_PATH = "./data/TN_Agriculture_FarmersWelfare_PolicyNote_2023-24.pdf"  # Ensure this matches your actual PDF filename

if not os.path.exists(PDF_PATH):
    raise FileNotFoundError(f"❌ PDF file '{PDF_PATH}' not found in directory!")

print(f"📖 Loading PDF: {PDF_PATH}...")
loader = PyPDFLoader(PDF_PATH)
raw_docs = loader.load()

# 4. Chunk Document for LLM Entity Extraction
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
docs = text_splitter.split_documents(raw_docs)
print(f"✂️ Created {len(docs)} text chunks for graph processing.")

# 5. Define Allowed Graph Ontology Schema
llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")

allowed_nodes = ["Scheme", "Category", "Beneficiary", "Subsidy", "Document", "Department"]
allowed_relationships = ["BELONGS_TO", "TARGETS", "OFFERS", "REQUIRES", "MANAGED_BY"]

llm_transformer = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=allowed_nodes,
    allowed_relationships=allowed_relationships
)

# 6. Extract Graph Entities via OpenAI LLM
print("🤖 Extracting Entities and Relationships using OpenAI...")
graph_documents = llm_transformer.convert_to_graph_documents(docs[:20])  # Test run on first 20 chunks

# 7. Ingest into Neo4j Cloud
print("🚀 Uploading Graph Nodes and Edges to Neo4j AuraDB...")
graph.add_graph_documents(graph_documents)

print("✅ Knowledge Graph Ingestion Completed Successfully!")