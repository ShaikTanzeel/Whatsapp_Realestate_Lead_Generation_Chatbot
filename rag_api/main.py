import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict
from langchain_core.messages import HumanMessage, AIMessage

# Why: FastAPI runs from context of directory, adding this ensures local 'rag_engine' imports resolve correctly.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_engine.sql_agent import SQLAgent

app = FastAPI(
    title="Bilingual WhatsApp Real Estate RAG API",
    description="FastAPI bridge hosting the SQL Agent and DuckDB analytics database.",
    version="1.0.0"
)

# Why: ChatMessage schema mirrors n8n's array payloads, establishing a reliable schema contract.
class ChatMessage(BaseModel):
    role: str = Field(..., description="Sender identity. Handled as 'user' or 'assistant'.")
    content: str = Field(..., description="Message string.")

# Why: QueryRequest structure defines contract for n8n HTTP Request node post-security execution.
class QueryRequest(BaseModel):
    question: str = Field(..., description="Cleaned customer query.")
    chat_history: Optional[List[Union[ChatMessage, Dict[str, str], List[str]]]] = Field(
        default=[],
        description="Thread context containing past interactions."
    )

# Why: QueryResponse schema formats returned data for WhatsApp-compatible text rendering.
class QueryResponse(BaseModel):
    response: str = Field(..., description="Formatted investment hook.")
    sql: str = Field(..., description="Executed SQL query (used for trace logs).")

# Why: Resolves references, context, and pronouns.
# Connectivity: Translates generic n8n context payloads into LangChain's native Message objects for LLM consumption.
def parse_chat_history(history_inputs) -> List[Union[HumanMessage, AIMessage]]:
    parsed = []
    if not history_inputs:
        return parsed

    for item in history_inputs:
        if isinstance(item, ChatMessage):
            role = item.role.lower()
            content = item.content
        elif isinstance(item, dict):
            role = item.get("role", "user").lower()
            content = item.get("content", "")
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            role = str(item[0]).lower()
            content = str(item[1])
        else:
            continue

        if role in ("user", "human"):
            parsed.append(HumanMessage(content=content))
        elif role in ("assistant", "ai"):
            parsed.append(AIMessage(content=content))
            
    return parsed

# Why: Simple diagnostic hook.
# Connectivity: Used by Docker Compose to verify that the transactions.duckdb database volume is mounted successfully.
@app.get("/health", tags=["Health"])
async def health_check():
    db_path = os.getenv("DB_PATH", "/app/data/transactions.duckdb")
    db_exists = os.path.exists(db_path)
    return {
        "status": "healthy",
        "database_connected": db_exists,
        "db_path": db_path
    }

# Why: Core service gateway.
# Connectivity: Receives prompt-sanitized inputs from n8n, queries DuckDB database, and passes results back to the Yara flow.
@app.post("/query", response_model=QueryResponse, tags=["Agent"])
async def run_query(payload: QueryRequest):
    try:
        # Step 1: Map memory structures
        chat_history = parse_chat_history(payload.chat_history)
        
        # Step 2: Initialize analytics orchestrator
        agent = SQLAgent()
        
        # Step 3: Run pipeline: Question -> SQL -> DuckDB Execution -> Professional Report
        report, df = agent.ask(payload.question, chat_history=chat_history)
        
        # Why: Store executed query state for tracing n8n execution errors.
        sql_query = getattr(agent, "last_sql", "No SQL generated")
        
        return QueryResponse(
            response=report,
            sql=sql_query
        )
    except Exception as e:
        # Why: Catches db or llm pipeline failures, returning HTTP 500 to n8n triggers.
        raise HTTPException(
            status_code=500,
            detail=f"Error in RAG SQL Agent service: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
