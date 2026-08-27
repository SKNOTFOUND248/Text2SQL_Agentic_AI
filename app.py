import os
import sys
import uuid
import requests
import streamlit as st
from PIL import Image

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

FASTAPI_URL = "http://localhost:8000"

# Set Page Config
st.set_page_config(
    page_title="Advanced SQL Multi-Agent App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Design aesthetics
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

/* Global Font Override */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif;
}

/* Gradient Header */
.header-container {
    background: linear-gradient(135deg, #6366F1, #EC4899, #F59E0B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 3.2rem;
    text-align: center;
    margin-bottom: 0.1rem;
    letter-spacing: -0.05rem;
}

.subheader-text {
    font-size: 1.2rem;
    color: #9CA3AF;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 300;
}

/* Glassmorphic Container Cards */
.agent-card {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
}

.agent-title {
    background: linear-gradient(135deg, #a855f7, #6366f1);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 30px;
    font-size: 0.85rem;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 0.8rem;
    box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
}

/* Status Badges */
.status-badge-safe {
    background-color: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
}

.status-badge-unsafe {
    background-color: rgba(239, 68, 68, 0.15);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
}

/* Code block customization */
code {
    background-color: rgba(0, 0, 0, 0.4) !important;
    border-radius: 4px;
    padding: 0.1rem 0.3rem;
}

/* Chat bubble styling for history */
.history-user {
    background-color: rgba(99, 102, 241, 0.1);
    border-left: 4px solid #6366F1;
    padding: 0.8rem;
    margin-bottom: 0.8rem;
    border-radius: 0 8px 8px 0;
}

.history-assistant {
    background-color: rgba(255, 255, 255, 0.02);
    border-left: 4px solid #EC4899;
    padding: 0.8rem;
    margin-bottom: 1.5rem;
    border-radius: 0 8px 8px 0;
}
</style>
""", unsafe_allow_html=True)

# Initialize Session ID
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# Sidebar Configuration
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
    st.markdown("### 🗄️ SQL Multi-Agent App")
    st.markdown("---")
    
    # Session Management
    st.markdown("#### Session Manager")
    
    # Retrieve all sessions from backend
    try:
        res = requests.get(f"{FASTAPI_URL}/api/history")
        if res.status_code == 200:
            session_list = res.json()
        else:
            session_list = []
    except Exception:
        session_list = []
        
    # Ensure current session is in list or add it
    if st.session_state["session_id"] not in session_list:
        display_sessions = [st.session_state["session_id"]] + session_list
    else:
        display_sessions = session_list
        
    selected_sess = st.selectbox(
        "Active Session ID",
        options=display_sessions,
        index=display_sessions.index(st.session_state["session_id"])
    )
    
    if selected_sess != st.session_state["session_id"]:
        st.session_state["session_id"] = selected_sess
        st.rerun()
        
    if st.button("➕ Start New Session", use_container_width=True):
        st.session_state["session_id"] = str(uuid.uuid4())
        st.success("Started new session!")
        st.rerun()
        
    st.markdown("---")
    st.markdown("#### 📊 Database Information")
    st.info("""
    **Connection**: SQLite
    **Target DB**: `my_database.db`
    **Tables**:
    - `users`
      - `id` (INTEGER) - Primary Key
      - `name` (TEXT) - Username
      - `age` (INTEGER) - Age of user
    """)
    st.markdown("---")
    st.caption("Advanced Agentic System built with DSPy, LangGraph, FastAPI & Celery")

# Main Header Design
st.markdown('<div class="header-container">SQL Multi-Agent Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader-text">Securely query, execute, plot, and analyze database tables using LangGraph-driven workflows</div>', unsafe_allow_html=True)

# User Query input form
st.markdown("### Ask a Database Question")
with st.form("query_form", clear_on_submit=False):
    query_input = st.text_area(
        "Describe what you want to retrieve or visualize:",
        placeholder="Example: 'Show a bar chart of users and their ages' or 'What is the average age of users?'",
        height=80
    )
    submit_button = st.form_submit_button("🚀 Run Workflow", use_container_width=True)

# Handle Query Execution
if submit_button:
    if not query_input.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Executing multi-agent workflow (rewriting, querying database, generating plots)..."):
            try:
                # Trigger FastAPI query
                payload = {
                    "session_id": st.session_state["session_id"],
                    "user_request": query_input
                }
                response = requests.post(f"{FASTAPI_URL}/api/query", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 1. Display Final Answer
                    st.success("### Final Answer")
                    st.markdown(f"**{data['final_answer']}**")
                    st.markdown("---")
                    
                    # 2. Display Detailed Report
                    st.markdown("### Detailed Analytical Report")
                    st.markdown(data["report_markdown"])
                    
                    # Render Visual plot if generated
                    if data["visualization_generated"] and data["visualization_path"] != "None":
                        st.markdown("#### Generated Visual Analysis Plot")
                        # Load file locally
                        filename = os.path.basename(data["visualization_path"])
                        local_plot_path = os.path.join(BASE_DIR, "static", "plots", filename)
                        if os.path.exists(local_plot_path):
                            try:
                                image = Image.open(local_plot_path)
                                st.image(image, caption="Agent Generated Visualization", use_container_width=True)
                            except Exception as img_err:
                                st.error(f"Could not load generated plot image locally: {img_err}")
                        else:
                            # Fallback to loading via HTTP from FastAPI
                            st.image(f"{FASTAPI_URL}{data['visualization_path']}", caption="Agent Generated Visualization", use_container_width=True)
                    st.markdown("---")
                    
                    # 3. Agent Execution Details (Accordions)
                    st.markdown("### 🛠️ Agent Thought Process & Steps")
                    
                    with st.expander("Step 1: SQL Query Planner & Security Sanitizer (QueryRewriter Agent)"):
                        st.markdown(f"""
                        <div class="agent-card">
                            <div class="agent-title">QueryRewriter Agent</div><br/>
                            <b>Safety Check Result</b>: 
                            <span class="{'status-badge-safe' if data['safety_flag'] == 1 else 'status-badge-unsafe'}">
                                {'SAFE' if data['safety_flag'] == 1 else 'UNSAFE/INSUFFICIENT'}
                            </span><br/><br/>
                            <b>Sanitized / Rewritten Request</b>:<br/>
                            <i>"{data['modified_request']}"</i><br/><br/>
                            <b>Agent Message</b>:<br/>
                            {data['rewriter_message']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with st.expander("Step 2: Database Query Executor (QueryRunner Agent)"):
                        st.markdown(f"""
                        <div class="agent-card">
                            <div class="agent-title">QueryRunner Agent</div><br/>
                            <b>Executed SQL Query</b>:
                            <pre><code>{data['sql_query']}</code></pre>
                            <b>SQL Result Payload</b>:
                            <pre><code>{data['sql_results']}</code></pre>
                            <b>Execution Messages</b>:<br/>
                            {data['executor_message']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with st.expander("Step 3: Visualizer & Plot Creator (VisualAnalysis Agent)"):
                        st.markdown(f"""
                        <div class="agent-card">
                            <div class="agent-title">VisualAnalysis Agent</div><br/>
                            <b>Visualization Attempted</b>: {"Yes" if data['visualization_generated'] else "No"}<br/><br/>
                            <b>Generated Matplotlib/Seaborn Python Code</b>:
                            <pre><code>{data['visual_code']}</code></pre>
                            <b>Visualizer Message</b>:<br/>
                            {data['visual_message']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                else:
                    st.error(f"Error executing agent workflow: {response.text}")
                    
            except Exception as e:
                st.error(f"Failed to communicate with the FastAPI backend: {e}")
                st.info("Make sure the FastAPI backend and Celery worker are running.")

# Render Chat History in Session
st.markdown("---")
st.markdown("### 💬 Session Chat History")

try:
    history_res = requests.get(f"{FASTAPI_URL}/api/history/{st.session_state['session_id']}")
    if history_res.status_code == 200:
        history_data = history_res.json()
        if not history_data:
            st.info("No query logs in this session yet.")
        else:
            for item in history_data:
                st.markdown(f"""
                <div class="history-user">
                    <b>User (Prompt):</b> {item['user_request']}<br/>
                    <small>Time: {item['timestamp']}</small>
                </div>
                <div class="history-assistant">
                    <b>Assistant (Answer):</b> {item['final_answer']}<br/>
                    <b>SQL Query Run:</b> <code>{item['sql_query']}</code>
                </div>
                """, unsafe_allow_html=True)
                # Show thumbnails of historic plots
                if item['visualization_path'] != "None":
                    plot_filename = os.path.basename(item['visualization_path'])
                    local_plot = os.path.join(BASE_DIR, "static", "plots", plot_filename)
                    if os.path.exists(local_plot):
                        st.image(local_plot, width=350, caption="Visual plot from history")
                    else:
                        st.image(f"{FASTAPI_URL}{item['visualization_path']}", width=350, caption="Visual plot from history")
    else:
        st.info("Could not load chat history.")
except Exception:
    st.info("No connection to history service.")
