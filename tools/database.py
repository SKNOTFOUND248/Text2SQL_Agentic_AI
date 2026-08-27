import os
import sqlite3

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "my_database.db"))

def SQLtool(query:str)-> str:
    """This function takes a SQL query as input and returns the result of the query as a string."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return str(result)

def PythonTool(code:str)-> str:
    """This function takes a Python code as input and returns the result of the code execution as a string."""
    try:
        exec_globals = {}
        exec(code, exec_globals)
        return str(exec_globals)
    except Exception as e:
        return str(e)
