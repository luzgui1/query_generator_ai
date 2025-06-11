#%%

from functions import aitools, utils, agents
# import google.generativeai as genai
from langchain_core.messages import HumanMessage, AIMessage
from functools import partial
import os
import logging

logging.basicConfig(
    filename="assistant.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filemode="a"
)

logger = logging.getLogger("GeminiAssistant")

# Load API key
creds_folder = r'C:\Users\guilherme.luz.NETSHOES\Desktop\codes\Credentials'
bq_creds = utils.get_credentials(creds_folder, "BQ")

# API do Gemini definido como variavel de ambiente

# Load Schema
description_path = r"data/context/data_description.md"
description = aitools.get_schema(description_path)

schema_path = r"data/context"

schema_list = []

def run_chatbot(user_input: str, user_name: str, chat_history: list = []):

    logger.info(f"[USER INPUT] ({user_name}) {user_input}")

    agentics = agents.GeminiAgents(doc=description,user_name=user_name)

    intention = agentics.classify_intent(user_input=user_input,memory=chat_history)

    preview_rows = []
    summary_response = ""
    generated_sql = None

    if intention in ["analysis-request","correction-request","include_schema"]:

        try:
            schema_choose = agentics.schema_chooser(user_input=user_input,schema_dir=schema_path)
            schema = schema_choose.get("schema","")
            schema_list.append(schema)  
        except:
            pass

        generated_sql = agentics.query_builder(intent=intention,user_input=user_input,schema=schema_list,memory=chat_history)

        #While loop para rodar a query 5x e corrigí-la até que funcione

        MAX_RETRIES = 5
        attempt = 0
        success = False

        current_sql = generated_sql
        
        while not success and attempt < MAX_RETRIES:
            try:
                # Tentativa de rodar a primeira query
                exec = aitools.run_query(current_sql, bq_creds)
                success = True

            except Exception as e:
                attempt += 1

                #Agente corrige o SQL com base no erro

                current_sql = agentics.query_fixer(user_input=user_input,error=str(e),schema=schema_list,memory=chat_history)
                generated_sql = current_sql

        if not success:
            logger.info(f"Query failed after {MAX_RETRIES} attempts:\n{current_sql}")

            raise RuntimeError(f"Query failed after {MAX_RETRIES} attempts:\n{current_sql}")

        preview_rows = exec.get("data_preview", [])
        table_view = "\n".join(str(row) for row in preview_rows)
        summary_response = agentics.final_response_builder(table=table_view,user_input=user_input,memory=chat_history)
        
    elif intention == 'explanation-request':
        schema_choose = agentics.schema_chooser(user_input,schema_path)
        selected_schema = schema_choose.get("schema","")        
        summary_response = agentics.general_response_builder(intent=intention,user_input=user_input,memory=chat_history,schema=selected_schema)

    else:
        summary_response = agentics.general_response_builder(intent=intention,user_input=user_input,memory=chat_history)

    return {
        "sql": generated_sql,
        "preview": preview_rows,
        "summary": summary_response,
    }

#%%