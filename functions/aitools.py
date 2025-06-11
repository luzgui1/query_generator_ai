from google.generativeai.types import FunctionDeclaration
from google.generativeai import GenerativeModel
from google.cloud import bigquery
import pandas as pd

## Schema Reader
read_schema = FunctionDeclaration(
    name = "read_schema",
    description=("Leia a documentação disponível para te auxiliar a compreender como construir queries " 
                "sempre que o usuário buscar por uma análise de dados"
                ),
    parameters={
        "type":"object",
        "properties": {
            "path":{
                "type":"string",
                "description":"O caminho para acessar a documentação disponível."
            }
        },
        "required":["path"]
    }
)

def get_schema(path):

    with open(path, "r", encoding="utf-8") as doc:
        schema = doc.read()

    return schema

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
        client = bigquery.Client.from_service_account_json(creds)
        print("Conexão com o BigQuery efetuada.")

        query_job = client.query(query)
        result = [dict(row) for row in query_job]
        dataframe = pd.DataFrame(result)

        return {"data_preview": dataframe.head(10).to_dict(orient="records")}

## Send data-to google bucket




