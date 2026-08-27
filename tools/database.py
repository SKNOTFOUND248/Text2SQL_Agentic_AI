import sqlite3


def SQLtool(query:str)-> str:
    """This function takes a SQL query as input and returns the result of the query as a string."""
    conn = sqlite3.connect("data\\my_database.db")
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
