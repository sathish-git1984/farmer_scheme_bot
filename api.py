# api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import json
from graph_rag import query_graph

app = FastAPI(
    title="TN Farmers Welfare Graph AI API",
    description="Backend API powered by Neo4j Knowledge Graph & LangChain",
    version="2.0.0"
)

# Enable CORS for Streamlit Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"
    detail_level: str = "Short"

@app.get("/")
def root():
    return {"status": "Online", "engine": "Neo4j Knowledge Graph RAG"}

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """Standard JSON response endpoint."""
    try:
        response = query_graph(request.query, request.detail_level)
        return {"response": response, "session_id": request.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
def chat_stream_endpoint(request: ChatRequest):
    """Streaming endpoint for Streamlit UI."""
    def event_stream():
        try:
            full_response = query_graph(request.query, request.detail_level)
            # Stream words chunk-by-chunk for smooth typing effect in UI
            words = full_response.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield chunk
        except Exception as e:
            yield f"⚠️ API Error: {str(e)}"

    return StreamingResponse(event_stream(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)