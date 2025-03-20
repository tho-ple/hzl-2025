import os
from openai import OpenAI
import sqlite3
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI client using environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Rest of your code remains unchanged

def get_all_tables():
    """Get a list of all tables in the database"""
    try:
        conn = sqlite3.connect('hauszumleben.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        return f"Database error: {str(e)}"

def get_table_schema(table_name):
    """Get the schema for a specific table"""
    try:
        conn = sqlite3.connect('hauszumleben.db')
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = cursor.fetchall()
        conn.close()
        
        columns = []
        for col in schema:
            columns.append({
                "name": col[1],
                "type": col[2],
                "not_null": bool(col[3]),
                "primary_key": bool(col[5])
            })
        return columns
    except Exception as e:
        return f"Database error: {str(e)}"

def query_database(query):
    try:
        conn = sqlite3.connect('hauszumleben.db')
        cursor = conn.cursor()
        
        # Get column names
        cursor.execute(query)
        column_names = [description[0] for description in cursor.description]
        
        # Fetch the data
        results = cursor.fetchall()
        
        # Convert to list of dictionaries for better readability
        formatted_results = []
        for row in results:
            formatted_results.append(dict(zip(column_names, row)))
        
        conn.close()
        return formatted_results
    except Exception as e:
        return f"Database error: {str(e)}"

def generate_response(prompt, model="gpt-3.5-turbo", concise=False):
    """Generate a response from OpenAI with option for concise output"""
    try:
        system_message = "You are an analyst who examines healthcare database information and provides clear insights and conclusions. Always respond in the same most probable language as the user's."
        if concise:
            system_message += " Keep your responses brief and focused only on the most important findings. Limit to 2-3 short paragraphs maximum."
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI API error: {str(e)}"

def get_database_structure():
    """Get the structure of the entire database without the data"""
    tables = get_all_tables()
    if isinstance(tables, str) and tables.startswith("Database error"):
        return tables
    
    database_structure = {}
    for table in tables:
        # Get table schema
        schema = get_table_schema(table)
        # Get row count
        row_count = query_database(f"SELECT COUNT(*) as count FROM {table}")[0]['count']
        
        database_structure[table] = {
            "schema": schema,
            "row_count": row_count
        }
    
    return database_structure

def generate_sql_for_question(question):
    """Use AI to generate appropriate SQL for the question"""
    # Get database structure for context
    db_structure = get_database_structure()
    
    prompt = f"""You are a SQL expert. Given the following database structure and user question, 
    generate the most appropriate SQL query to answer the question.
    
    Database structure:
    {json.dumps(db_structure, indent=2)}
    
    User question: "{question}"
    
    Return ONLY the SQL query with no explanations or markdown. The query should be directly executable in SQLite.
    """
    
    sql_query = generate_response(prompt)
    
    # Clean up the response to get just the SQL
    sql_query = sql_query.strip()
    if sql_query.startswith("```sql"):
        sql_query = sql_query[7:]
    if sql_query.endswith("```"):
        sql_query = sql_query[:-3]
    
    return sql_query.strip()

def smart_research_chatbot(question):
    """Conduct smart research across tables to answer a question"""
    # Step 1: Get database structure for context
    db_structure = get_database_structure()
    
    # Step 2: Generate SQL based on the question
    sql_query = generate_sql_for_question(question)
    
    # Step 3: Execute the query
    try:
        query_results = query_database(sql_query)
        
        # Step 4: Create a prompt with just the relevant data
        prompt = f"""Based on the following database structure and query results, please answer this question concisely: "{question}"
        
        Database structure:
        {json.dumps(db_structure, indent=2)}
        
        SQL Query used:
        {sql_query}
        
        Query results:
        {json.dumps(query_results, indent=2)}
        
        Provide ONLY the most important insights and direct answers. Be brief and to the point.
        Avoid lengthy explanations, background information, or repetition.
        """
        
        # Step 5: Generate the concise response
        return generate_response(prompt, concise=True)
    except Exception as e:
        return f"Error executing query: {str(e)}"
    
# Example usage
if __name__ == "__main__":
    question = "Which diet is the best one for sleep quality?"
    response = smart_research_chatbot(question)
    print(response)