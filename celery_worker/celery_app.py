import os
import sqlite3
from celery import Celery

# Define absolute paths for databases
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "tools", "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_DB = os.path.join(DATA_DIR, "chat_history.db")
BROKER_DB = os.path.join(DATA_DIR, "celery_broker.db")
RESULTS_DB = os.path.join(DATA_DIR, "celery_results.db")

# Format database URLs for Celery SQLAlchemy broker and backend
broker_url = f"sqla+sqlite:///{BROKER_DB.replace('\\', '/')}"
result_backend = f"db+sqlite:///{RESULTS_DB.replace('\\', '/')}"

app = Celery(
    "sql_chat_tasks",
    broker=broker_url,
    backend=result_backend
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True
)

@app.task(name="celery_app.save_chat_history")
def save_chat_history(session_id: str, user_request: str, sql_query: str, results: str, final_answer: str, visualization_path: str):
    """
    Asynchronous Celery task to save the details of a chat query to the SQLite history database.
    """
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()
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
        INSERT INTO chat_history (session_id, user_request, sql_query, results, final_answer, visualization_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, user_request, sql_query, results, final_answer, visualization_path))
    conn.commit()
    conn.close()
    return f"Successfully logged chat history for session {session_id} to database"
