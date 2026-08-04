# graph_rag.py
import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# 1. Load Environment Variables
load_dotenv()

neo4j_uri = os.getenv("NEO4J_URI")
if neo4j_uri and neo4j_uri.startswith("neo4j+s://"):
    neo4j_uri = neo4j_uri.replace("neo4j+s://", "neo4j+ssc://")

# 2. Initialize Neo4j Graph Connection
graph = Neo4jGraph(
    url=neo4j_uri,
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# Refresh schema to ensure LLM knows nodes and relationships
graph.refresh_schema()

# 3. Initialize OpenAI LLM
llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")

# 4. Improved Broad Cypher Generation Prompt
CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Search flexibly! Keywords might appear in Scheme names, Subsidies, Categories, or Beneficiaries.
Always use `toLower()` and `CONTAINS` for keyword matching across multiple node types.

Schema:
{schema}

Note: Do not include any explanations or markdown code blocks (```cypher) in the output.
Just return the Cypher statement directly.

Examples:
# What schemes offer subsidies for drip/micro irrigation?
MATCH (s:Scheme)
OPTIONAL MATCH (s)-[:OFFERS]->(sub:Subsidy)
OPTIONAL MATCH (s)-[:BELONGS_TO]->(c:Category)
WHERE toLower(s.id) CONTAINS 'drip' 
   OR toLower(s.id) CONTAINS 'micro' 
   OR toLower(s.id) CONTAINS 'irrigation'
   OR toLower(sub.id) CONTAINS 'drip'
   OR toLower(c.id) CONTAINS 'drip'
RETURN s.id AS Scheme, sub.id AS Offered_Subsidy, c.id AS Category

# What document is needed for drip irrigation?
MATCH (s:Scheme)
OPTIONAL MATCH (s)-[:REQUIRES]->(d:Document)
WHERE toLower(s.id) CONTAINS 'drip' OR toLower(s.id) CONTAINS 'micro'
RETURN s.id AS Scheme, d.id AS Required_Document

Question: {question}
Cypher Query:"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)

# 5. Create GraphCypherQAChain with Fallback
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    allow_dangerous_requests=True,
    return_intermediate_steps=True
)

def query_graph(query: str, detail_level: str = "Short") -> str:
    """Queries the Knowledge Graph and formats the output based on detail level."""
    
    mode_instructions = {
        "Short": "Keep response crisp, brief, and under 3 bullet points.",
        "Medium": "Provide a clear, balanced answer with key details and bullet points.",
        "Long": "Provide a comprehensive, detailed answer covering eligibility, documents, and benefits."
    }
    
    instruction = mode_instructions.get(detail_level, mode_instructions["Short"])
    full_prompt = f"{query}\n\nNote: {instruction}"

    try:
        response = chain.invoke({"query": full_prompt})
        result_text = response.get("result", "")
        
        # Fallback query if no Cypher records were matched
        if "don't know" in result_text.lower() or not result_text:
            fallback_cypher = """
            MATCH (n) 
            WHERE toLower(n.id) CONTAINS 'micro' OR toLower(n.id) CONTAINS 'irrigation' OR toLower(n.id) CONTAINS 'subsidy'
            RETURN labels(n) AS Type, n.id AS Name LIMIT 10
            """
            fallback_res = graph.query(fallback_cypher)
            if fallback_res:
                items = [f"- **{item['Type'][0]}**: {item['Name']}" for item in fallback_res]
                return f"Here are relevant schemes and subsidies found in the graph:\n\n" + "\n".join(items)
                
        return result_text
    except Exception as e:
        return f"Error executing Graph RAG: {str(e)}"

# 6. Direct Test Execution
if __name__ == "__main__":
    test_query = "What schemes offer subsidies for drip irrigation?"
    print(f"❓ Query: {test_query}\n")
    answer = query_graph(test_query, detail_level="Medium")
    print(f"\n💡 Answer:\n{answer}")