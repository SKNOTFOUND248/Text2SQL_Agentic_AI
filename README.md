# Advanced SQL Multi-Agent System

This repository contains a production-grade, multi-agent SQL database querying, visualization, and analytical reporting application. The system is built using DSPy for agent implementation, LangGraph for workflow orchestration, FastAPI for the backend service layer, Celery for asynchronous chat history logging, and Streamlit for the presentation layer.

## Architecture Overview

The system uses a decoupled, event-driven multi-agent design. The backend manages state using a directed state graph and offloads history database writes to an asynchronous task queue.

### Technical Stack
- Agent Declaration: DSPy (programming over prompting paradigm)
- Workflow Orchestration: LangGraph (StateGraph model)
- Background Task Processing: Celery (with SQLite broker and backend)
- Database Layer: SQLite3 (for both source data and chat logs)
- Backend Service: FastAPI (Asynchronous API gateway)
- Frontend Presentation: Streamlit (Interactive dashboard)

---

## LangGraph Workflow Design

The core execution path is modeled as a LangGraph StateGraph. The workflow maintains a shared state dictionary containing the session ID, query details, SQL logs, raw outputs, visualization paths, and reports.

### Workflow Nodes and Execution Steps

1. Rewriter Node:
   - Agent: Query Planner and Security Sanitizer (Query_safty_agent using DSPy ChainOfThought)
   - Responsibility: Inspects the incoming request against the schema. Strips out SQL injection vectors, refactors the query for database compliance, and sets a safety flag (1 for safe, 0 for unsafe or insufficient details).

2. Executor Node:
   - Agent: Database Executor (QueryExecutor using DSPy ReAct)
   - Responsibility: Runs if the safety flag is 1. Evaluates the modified request, selects SQLtool, executes queries on the SQLite database, and returns the result tuple list. If an execution error occurs, it catches the exception and attempts self-correction.

3. Visual Analysis Node:
   - Agent: Visualizer (VisualAnalysis using DSPy ChainOfThought)
   - Responsibility: Inspects the original request to identify plotting requirements. If a visual chart is requested, it generates Python code using Matplotlib and Seaborn. The system executes the code in an isolated local namespace and saves the plot as a PNG image in the static directory.

4. Report Node:
   - Agent: Reporter (ReportCreation using DSPy ChainOfThought)
   - Responsibility: Compiles the query, schema, executed SQL, raw output tuple list, and chart references into a structured Markdown document containing data tables and image linkages.

5. Final Answer Node:
   - Agent: Coordinator (FinalAnswer using DSPy ChainOfThought)
   - Responsibility: Synthesizes the final response to the user, providing a high-level summary of the findings and confirming the generated assets.

### Conditional Routing Logic
A conditional edge is placed after the Rewriter Node.
- If the safety flag is 1, execution routes to the Executor Node.
- If the safety flag is 0, execution bypasses the Executor and Visualizer nodes, routing directly to the Report Node to summarize the warning or data limitation.

---

## Background Chat History Logging with Celery

To prevent local disk I/O operations from blocking the web server response lifecycle, chat logging is handled asynchronously.

- Setup: Celery is configured with an SQLAlchemy broker (`sqla+sqlite:///`) and an SQLite database backend. This avoids external dependencies like Redis or RabbitMQ, making the deployment fully portable.
- Execution: Once the LangGraph workflow completes, the FastAPI route triggers the Celery worker task (`save_chat_history.delay(...)`) and immediately returns the results to the user.
- Storage: The Celery worker runs in its own process, creating a `chat_history.db` SQLite database and writing log entries (session ID, timestamp, prompt, SQL statement, result tuples, final summary, and plot paths) asynchronously.

---

## Interview-Ready Deep Dives

### Why use LangGraph instead of sequential script execution?
LangGraph provides a formal framework for building stateful, multi-agent systems with cycles and conditional routing. In a sequential script, implementing safety bypasses or agent self-correction loops results in complex branching code. LangGraph modularizes agents into independent nodes and defines transitions using explicit edges.

### Why use DSPy instead of traditional string prompt templates?
DSPy treats prompts as parameters to be compiled and optimized. Instead of manually tweaking prompts for different LLMs, DSPy agents are defined by Pydantic-like signatures (inputs and outputs). This separation of concerns allows developers to swap underlying models (e.g., from local Ollama Qwen to OpenAI GPT) without rewriting prompts, as the system compiles the optimal prompt format automatically.

### Why is the Executor agent implemented with ReAct instead of Chain of Thought?
The database executor needs to interact with external tools (such as executing SQL queries). A Chain of Thought (CoT) agent only generates text outputs in a single pass. A ReAct (Reasoning and Acting) agent works in a loop: it generates a thought, executes a tool (SQLtool), reads the database feedback, and updates its strategy. If the database returns a syntax error, the ReAct loop allows the agent to self-correct and execute a revised query.

---

## Application Interface and Screenshots

The presentation layer is built as a dark-mode Streamlit dashboard that visualizes each phase of the agent workflow.

### User Interface and Visual Plotting
The dashboard provides a text area to enter natural language queries and displays the agent steps dynamically.

Reference:
- User Interface Layout:
  ![Dashboard Query Interface](test_img/Screenshot%202026-08-27%20110902.png)
  This screenshot demonstrates the main UI layout, showing the chat input panel, sidebar database schema documentation, and session management selectors.

- Matplotlib / Seaborn Chart Rendering:
  ![Visual Plot Output](test_img/Screenshot%202026-08-27%20111558.png)
  This screenshot shows a bar chart representing user age distributions, generated dynamically by the VisualAnalysis agent and rendered on the dashboard.

### Step-by-Step Agent Trace
The dashboard uses interactive components to trace the reasoning of each agent node.

Reference:
- Security and Optimization (Rewriter Agent):
  ![Rewriter Agent Output](test_img/Screenshot%202026-08-27%20111505.png)
  This screenshot shows the QueryRewriter output, verifying the query safety status, security classification, and refined database request.

- Database Execution (QueryRunner Agent):
  ![QueryRunner Agent Output](test_img/Screenshot%202026-08-27%20111516.png)
  This screenshot displays the compiled SQL query, execution status, and the raw SQLite output tuple list.

- Python Plotting Logic (VisualAnalysis Agent):
  ![Visualizer Agent Output](test_img/Screenshot%202026-08-27%20111545.png)
  This screenshot shows the python code generated by the agent to construct the matplotlib visualization.

- Historical Chat Sessions:
  ![Session Chat History](test_img/Screenshot%202026-08-27%20111608.png)
  This screenshot demonstrates the sidebar session manager and the loaded chat history log retrieved from the SQLite database.

---

## Installation and Setup

1. Setup the Virtual Environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Run the Celery Background Task Worker:
   ```bash
   .venv\Scripts\celery -A celery_worker.celery_app worker --loglevel=info -P solo
   ```

3. Start the FastAPI Service:
   ```bash
   .venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

4. Launch the Streamlit Dashboard:
   ```bash
   .venv\Scripts\python -m streamlit run app.py
   ```
