import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Import both the non-streaming and streaming functions from your engine
from guardrails import check_guardrail
from rag_engine import ask_farmer_bot, ask_farmer_bot_stream

load_dotenv()

app = FastAPI(
    title="Tamil Nadu Farmers Welfare Scheme AI API",
    description="Backend API powered by LangChain, OpenAI, and ChromaDB.",
    version="1.0"
)

# Request Data Model
class QueryRequest(BaseModel):
    query: str
    session_id: str = "default_session"
    detail_level: str = "Short"  # Options: Short, Medium, Long
    
# Response Data Model for non-streaming endpoint
class QueryResponse(BaseModel):
    answer: str
    status: str

@app.get("/")
def root():
    return {"message": "TN Farmers Welfare AI Bot API is running!"}

# ==========================================
# 1. Non-Streaming Endpoint (Returns Full JSON)
# ==========================================
@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    # Process query through RAG engine (includes internal guardrail check)
    answer = ask_farmer_bot(
        query=request.query, 
        session_id=request.session_id,
        detail_level=request.detail_level
    )
    
    return QueryResponse(answer=answer, status="success")

# ==========================================
# 2. Streaming Endpoint (Token-by-Token)
# ==========================================
@app.post("/chat/stream")
async def chat_stream_endpoint(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # A. Guardrail check
    is_allowed, rejection_msg = check_guardrail(request.query)
    if not is_allowed:
        async def generate_rejection():
            yield rejection_msg
        return StreamingResponse(generate_rejection(), media_type="text/plain")

    # B. Generator function streaming chunks from RAG engine
    async def event_generator():
        for chunk in ask_farmer_bot_stream(
            query=request.query,
            session_id=request.session_id,
            detail_level=request.detail_level
        ):
            yield chunk
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    # Start server on http://localhost:8000
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)