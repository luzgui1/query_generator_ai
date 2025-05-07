from google.generativeai.types import FunctionDeclaration
from google.generativeai import GenerativeModel
from google.cloud import bigquery
import pandas as pd

### Query Builder

def get_schema(path):

    with open(path, "r", encoding="utf-8") as doc:
        schema = doc.read()

    return schema

generate_query = FunctionDeclaration(
    name="generate_query",
    description="Generates a SQL SELECT query based on internal documentation and user request.",
    parameters={
        "type": "object",
        "properties": {
            "user_request": {
                "type": "string",
                "description": "The user request needing translation to SQL."
            }
        },
        "required": ["user_request"]
    }
)

def build_query(user_request: str,schema_text):

    doc_model = GenerativeModel(model_name="models/gemini-1.5-flash")

    prompt = f"""
    You are an expert data analyst working with Google BigQuery.

    Always use Google BigQuery documentation to build your queries.

    Here is the internal schema documentation:
    \"\"\"
    {schema_text}
    \"\"\"

    Based on that, generate the most accurate SELECT statement (BigQuery) to fulfill this request:
    \"{user_request}\"

    You have expert knowledge of how to write efficient SQL for BigQuery. Avoid SELECT *.

    Only return the SQL query itself, without triple backticks or Markdown formatting.
    """

    response = doc_model.generate_content(prompt)

    # Extract text from response
    query = response.text.strip()

    return {"query": query}

## Query executor

execute_query = FunctionDeclaration(
    name="execute_query",
    description="Executes a SQL statement in BigQuery and returns a preview of the result.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The SQL query to run in BigQuery."
            }
        },
        "required": ["query"]
    }
)

def run_query(query: str,creds):
    try:
        client = bigquery.Client.from_service_account_json(creds)
        print("Conexão com o BigQuery efetuada.")

        query_job = client.query(query)
        result = [dict(row) for row in query_job]
        dataframe = pd.DataFrame(result)

        return {"data_preview": dataframe.head(10).to_dict(orient="records")}

    except Exception as e:
        print(f"Erro ao executar consulta: {e}")
        return {"error": str(e)}

## Send data-to google bucket




