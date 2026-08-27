import os
import sys
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from Graph.graph import app_graph
from celery_worker.celery_app import save_chat_history, HISTORY_DB

app = FastAPI(
    title="Advanced SQL Multi-Agent Backend",
    description="FastAPI service for Multi-Agent database querying and visualization",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure folders exist
os.makedirs(os.path.join(BASE_DIR, "static", "plots"), exist_ok=True)

# Mount static directory for visualization plots
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Request / Response Schemas
class QueryRequest(BaseModel):
    session_id: str
    user_request: str

class QueryResponse(BaseModel):
    session_id: str
    user_request: str
    database_schema: Optional[str]
    modified_request: Optional[str]
    rewriter_message: Optional[str]
    safety_flag: int
    sql_query: Optional[str]
    sql_results: Optional[str]
    executor_message: Optional[str]
    visual_code: Optional[str]
    visualization_path: Optional[str]
    visual_message: Optional[str]
    visualization_generated: bool
    report_markdown: Optional[str]
    final_answer: Optional[str]

# ==========================================
# FastAPI Endpoints
# ==========================================

@app.post("/api/query", response_model=QueryResponse)
async def handle_query(payload: QueryRequest):
    """
    Run the Multi-Agent SQL analysis workflow.
    Invokes the LangGraph workflow, triggers celery log task, and returns the full state.
    """
    try:
        # Run LangGraph workflow
        initial_state = {
            "session_id": payload.session_id,
            "user_request": payload.user_request
        }
        
        # invoke returns the final state of the graph
        output_state = app_graph.invoke(initial_state)
        
        # Async Celery task to store chat history in background
        save_chat_history.delay(
            session_id=payload.session_id,
            user_request=output_state.get("user_request"),
            sql_query=output_state.get("sql_query") or "None",
            results=output_state.get("sql_results") or "None",
            final_answer=output_state.get("final_answer") or "Could not process request",
            visualization_path=output_state.get("visualization_path") or "None"
        )
        
        # Return graph outputs aligned to response schema
        return QueryResponse(
            session_id=payload.session_id,
            user_request=output_state.get("user_request"),
            database_schema=output_state.get("schema"),
            modified_request=output_state.get("modified_request"),
            rewriter_message=output_state.get("rewriter_message"),
            safety_flag=output_state.get("safety_flag", 0),
            sql_query=output_state.get("sql_query"),
            sql_results=output_state.get("sql_results"),
            executor_message=output_state.get("executor_message"),
            visual_code=output_state.get("visual_code"),
            visualization_path=output_state.get("visualization_path"),
            visual_message=output_state.get("visual_message"),
            visualization_generated=output_state.get("visualization_generated", False),
            report_markdown=output_state.get("report_markdown"),
            final_answer=output_state.get("final_answer")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph Execution Error: {str(e)}")


@app.get("/api/history/{session_id}")
def get_session_history(session_id: str):
    """
    Retrieve chat log history for a specific session ID.
    """
    if not os.path.exists(HISTORY_DB):
        return []
    
    try:
        conn = sqlite3.connect(HISTORY_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Ensure table exists (in case celery worker hasn't run it yet)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_request TEXT,
                sql_query TEXT,
                results TEXT,
                final_answer TEXT,
                visualization_path TEXT
            )
        """)
        
        cursor.execute("""
            SELECT * FROM chat_history 
            WHERE session_id = ? 
            ORDER BY timestamp DESC
        """, (session_id,))
        
        rows = cursor.fetchall()
        history = [dict(row) for row in rows]
        conn.close()
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Read Error: {str(e)}")


@app.get("/api/history")
def get_all_history():
    """
    Retrieve all session IDs that have history.
    """
    if not os.path.exists(HISTORY_DB):
        return []
        
    try:
        conn = sqlite3.connect(HISTORY_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history';")
        if not cursor.fetchone():
            conn.close()
            return []
            
        cursor.execute("SELECT DISTINCT session_id FROM chat_history ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        sessions = [row[0] for row in rows]
        conn.close()
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Read Error: {str(e)}")
