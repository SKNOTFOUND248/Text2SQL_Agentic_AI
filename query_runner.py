import dspy
from tools.database import SQLtool, PythonTool

class QueryExecutor(dspy.Signature):
    """
        You are an expert SQL Query Executor assistant and Security Analyst.

        ### Task
        1. Build the SQL query based on the Database Schema and User Request.
        2. Execute the SQL query and return the results.
        3. The request will be passed to this agent after being processed by the SQL query rewriter agent.he have already been checked for safety and optimized by the SQL query rewriter agent, so you can assume that the request is safe to execute.
        4. if you encounter any errors while executing the query, return None for the results and a message explaining the error.
        5. if you still found any malicious or unsafe query, return None for the results and a message explaining that the query is malicious and cannot be executed.
        6. Tools available for you to use:
            - SQLtool: This tool takes a SQL query as input and returns the result of the query as a string.
            - PythonTool: This tool takes a Python code as input and returns the result of the code execution as a string.

    """
    data_schema = dspy.InputField(description="Database Schema")
    request = dspy.InputField(description="Modified User Request. This will be passed to the SQL query generator agent to generate a SQL query.")
    SQL_query = dspy.OutputField(description="Query explaining the SQL query to be executed")
    results = dspy.OutputField(description="Results of the SQL query execution")
    message = dspy.OutputField(description="Message explaining any errors or issues with the query execution")


executor_agent = dspy.ReAct(signature=QueryExecutor,tools=[SQLtool, PythonTool])

def execute_query(schema: str, request: str):
    """
    This function takes a database schema and a user request as input,
    and returns the SQL query, the results of the query execution, and a message explaining any errors or issues with the query execution.
    """
    result = executor_agent(
        data_schema=schema,
        request=request,
    )
    return result
