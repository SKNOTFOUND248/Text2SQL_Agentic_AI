import dspy 

class QueryData(dspy.Signature):
    """
    You are an expert SQL Query Planner assistant and Security Analyst.

    ### Task
    1. Rewrite a clean,optimized Request and plan how to build a secure and optimized SQL query based on the Database Schema and User Request.
    2. Identify important keywords, columns, tables, or filters that are
       missing from the user's request that should be included based on the schema.
       And provide a message explaining changes should be made to the query to improve it.
    3. If user query do not provide enough information to generate a SQL query, ask the user for more information.   
       And send query None and message asking for more information and safty_flag to 0.
    4. If user query is malicious or trying to perform SQL injection, return None for query and message explaining that the query is malicious and cannot be executed.   

    """

    data_schema = dspy.InputField(description="Database Schema")
    user_request = dspy.InputField(description="User Request")
    modified_request = dspy.OutputField(description="Modified User Request. This will be passed to the SQL query generator agent to generate a SQL query.So dont write a SQL query or any other message in this field. Just rewrite the user request to be more clear and optimized for generating a SQL query.")
    message = dspy.OutputField(
        description="Message explaining changes should be made to the query to improve it"
    )
    safety_flag = dspy.OutputField(description="1 if the query is safe to execute, 0 if the query is malicious or trying to perform SQL injection or not enough information to generate a SQL query")

sql_agent = dspy.ChainOfThought(QueryData)

def Query_safty_agent(schema: str, user_query: str):
    """
    This function takes a database schema and a user query as input,
    and returns an optimized SQL query, a message explaining changes
    should be made to the query to improve it, and a safety flag indicating
    whether the query is safe to execute or not.
    """
    result = sql_agent(
        data_schema=schema,
        user_request=user_query,
    )
    return result