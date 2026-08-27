import os
import sys
import uuid
import sqlite3
from typing import TypedDict, Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import llmconfig
import dspy
from langgraph.graph import StateGraph, END

# Import existing agents
from rewriter_agent import Query_safty_agent
from query_runner import execute_query

# ==========================================
# DSPy Signatures for New Agents
# ==========================================

class VisualAnalysis(dspy.Signature):
    """
    You are an expert Data Visualizer.
    Based on the User Request, the SQL Query, and the SQL Results, determine if a visualization (like a bar chart, line chart, pie chart, etc.) is appropriate.
    If a visualization is needed:
    1. Write clean, complete Python code using matplotlib and seaborn to plot the data.
    2. The results are passed as a string representation of a list of tuples (e.g. "[(1, 'Alice', 25), (2, 'Bob', 30)]"). Parse this string in your Python code using ast.literal_eval.
    3. The columns are: 'id', 'name', 'age' for the 'users' table.
    4. Save the figure to the exact filepath provided in 'plot_filepath'.
    5. Return the python code in the 'python_code' field.
    6. Set 'visualization_generated' to True.
    If no visualization is appropriate or data cannot be plotted (e.g. text search, empty list, or single value), set 'python_code' to None and 'visualization_generated' to False.
    """
    request = dspy.InputField(description="Original or modified user request")
    sql_query = dspy.InputField(description="SQL query executed")
    sql_results = dspy.InputField(description="Results of the SQL query as a string")
    plot_filepath = dspy.InputField(description="File path where the generated plot must be saved")
    
    python_code = dspy.OutputField(description="Python code to generate and save the plot, or None if no plot is needed")
    visualization_generated = dspy.OutputField(description="Boolean (True/False) indicating if a visualization was generated")
    message = dspy.OutputField(description="Reasoning/Message explaining the visualization or why it's not needed")


class ReportCreation(dspy.Signature):
    """
    You are an expert Data Analyst and Technical Writer.
    Generate a detailed Markdown report summarizing the analysis of the user's query:
    1. User's query and the analytical goal.
    2. SQL query executed to retrieve the data.
    3. Structured markdown table of the results (format the data cleanly).
    4. An analytical explanation of the findings (e.g. age distributions, averages, details).
    5. Mention of the generated visualization plot if one was created, referencing it via markdown image syntax.
       The image path should be the exact value of the visualization_path, e.g. if visualization_path is `/static/plots/plot_xyz.png`, reference it in markdown as `![User Ages](/static/plots/plot_xyz.png)`.
    """
    request = dspy.InputField(description="Original or modified user request")
    sql_query = dspy.InputField(description="SQL query executed")
    sql_results = dspy.InputField(description="Results of the SQL query as a string")
    visualization_path = dspy.InputField(description="Path to the generated visualization image, or 'None' if not generated")
    
    report_markdown = dspy.OutputField(description="Detailed markdown report summarizing the query, results, and visualization")


class FinalAnswer(dspy.Signature):
    """
    You are the lead Multi-Agent Coordinator.
    Provide a concise, user-friendly final answer to the user based on the generated report and the sql results.
    Summarize key findings in 2-3 sentences and explicitly mention if a chart/plot was generated.
    """
    user_request = dspy.InputField(description="Original user request")
    sql_results = dspy.InputField(description="SQL results")
    report_markdown = dspy.InputField(description="Detailed markdown report")
    visualization_path = dspy.InputField(description="Path to the generated visualization image, or 'None'")
    
    final_answer = dspy.OutputField(description="User-friendly final answer text summarizing findings")


# ==========================================
# Visualization Execution Helper
# ==========================================

def run_visualization_code(code: str, sql_results: str, plot_path: str) -> bool:
    import ast
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend safe for web apps
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    
    # Define local namespace for execution
    local_ns = {
        'plt': plt,
        'sns': sns,
        'ast': ast,
        'sql_results': sql_results,
        'plot_filepath': plot_path
    }
    
    try:
        plt.clf()
        plt.close('all')
        
        # Run agent's python code
        exec(code, {}, local_ns)
        
        # Fallback: Save if the file was not created but figure exists
        if not os.path.exists(plot_path):
            plt.savefig(plot_path)
            plt.close()
            
        return os.path.exists(plot_path)
    except Exception as e:
        print(f"Error executing visual code: {e}")
        return False


# ==========================================
# Schema Retrieval Helper
# ==========================================

def get_db_schema() -> str:
    from tools.database import DB_PATH
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema_parts = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            col_desc = [f"{col[1]} ({col[2]})" for col in columns]
            schema_parts.append(f"Table: {table_name}\nColumns: {', '.join(col_desc)}")
        conn.close()
        return "\n\n".join(schema_parts)
    except Exception as e:
        return f"Error retrieving schema: {e}"


# ==========================================
# LangGraph Workflow Setup
# ==========================================

class AgentState(TypedDict):
    session_id: str
    user_request: str
    schema: str
    
    # QueryRewriter outputs
    modified_request: Optional[str]
    rewriter_message: Optional[str]
    safety_flag: int  # 1 for safe, 0 for unsafe/insufficient info
    
    # QueryExecutor outputs
    sql_query: Optional[str]
    sql_results: Optional[str]
    executor_message: Optional[str]
    
    # VisualAnalysis outputs
    visual_code: Optional[str]
    visualization_path: Optional[str]
    visual_message: Optional[str]
    visualization_generated: bool
    
    # ReportCreation outputs
    report_markdown: Optional[str]
    
    # FinalAnswer outputs
    final_answer: Optional[str]


def rewriter_node(state: AgentState):
    schema = get_db_schema()
    result = Query_safty_agent(schema, state["user_request"])
    
    # Parse safety flag safely
    try:
        safety_flag = int(result.safety_flag)
    except:
        safety_flag = 0
        
    return {
        "schema": schema,
        "modified_request": result.modified_request,
        "rewriter_message": result.message,
        "safety_flag": safety_flag
    }


def executor_node(state: AgentState):
    if state.get("safety_flag", 0) == 0:
        return {}
        
    schema = state["schema"]
    req = state["modified_request"] or state["user_request"]
    result = execute_query(schema, req)
    
    return {
        "sql_query": result.SQL_query,
        "sql_results": result.results,
        "executor_message": result.message
    }


def visual_analysis_node(state: AgentState):
    if state.get("safety_flag", 0) == 0 or not state.get("sql_results"):
        return {
            "visual_code": None,
            "visualization_path": "None",
            "visual_message": "No visualization generated.",
            "visualization_generated": False
        }
        
    # Create static plots directory
    plots_dir = os.path.join(BASE_DIR, "static", "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    plot_filename = f"plot_{uuid.uuid4().hex[:8]}.png"
    plot_path = os.path.join(plots_dir, plot_filename)
    
    visual_agent = dspy.ChainOfThought(VisualAnalysis)
    result = visual_agent(
        request=state["user_request"],
        sql_query=state["sql_query"] or "",
        sql_results=state["sql_results"] or "",
        plot_filepath=plot_path
    )
    
    code = result.python_code
    generated = False
    
    is_gen_flag = str(result.visualization_generated).lower() in ("true", "1", "yes")
    
    if code and code.lower() != "none" and is_gen_flag:
        success = run_visualization_code(code, state["sql_results"], plot_path)
        if success:
            generated = True
            
    vis_url = f"/static/plots/{plot_filename}" if generated else "None"
    
    return {
        "visual_code": code if generated else None,
        "visualization_path": vis_url,
        "visual_message": result.message,
        "visualization_generated": generated
    }


def report_node(state: AgentState):
    if state.get("safety_flag", 0) == 0:
        report = f"### Request Processing Denied\n\n{state.get('rewriter_message', 'The query was classified as unsafe or insufficient information was provided.')}"
        return {"report_markdown": report}
        
    report_agent = dspy.ChainOfThought(ReportCreation)
    result = report_agent(
        request=state["modified_request"] or state["user_request"],
        sql_query=state["sql_query"] or "None",
        sql_results=state["sql_results"] or "None",
        visualization_path=state.get("visualization_path") or "None"
    )
    
    return {"report_markdown": result.report_markdown}


def final_answer_node(state: AgentState):
    final_agent = dspy.ChainOfThought(FinalAnswer)
    result = final_agent(
        user_request=state["user_request"],
        sql_results=state.get("sql_results") or "None",
        report_markdown=state.get("report_markdown") or "",
        visualization_path=state.get("visualization_path") or "None"
    )
    
    return {"final_answer": result.final_answer}


# Routing Condition
def route_after_rewriter(state: AgentState):
    if state.get("safety_flag", 0) == 1:
        return "executor"
    else:
        return "report"


# Assembling StateGraph
workflow = StateGraph(AgentState)

workflow.add_node("rewriter", rewriter_node)
workflow.add_node("executor", executor_node)
workflow.add_node("visual_analysis", visual_analysis_node)
workflow.add_node("report", report_node)
workflow.add_node("final_answer", final_answer_node)

workflow.set_entry_point("rewriter")

workflow.add_conditional_edges(
    "rewriter",
    route_after_rewriter,
    {
        "executor": "executor",
        "report": "report"
    }
)

workflow.add_edge("executor", "visual_analysis")
workflow.add_edge("visual_analysis", "report")
workflow.add_edge("report", "final_answer")
workflow.add_edge("final_answer", END)

app_graph = workflow.compile()
