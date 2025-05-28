#%%

from functions import aitools, utils, agents
import google.generativeai as genai
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
gemini_path = utils.get_credentials(creds_folder, "GEMINI")
bq_creds = utils.get_credentials(creds_folder, "BQ")

# Load Schema
description_path = r"data/context/data_description.md"
description = aitools.get_schema(description_path)

schema_path = r"data/context"

with open(gemini_path, 'r') as f:
    gemini_api_key = f.read().strip()

genai.configure(api_key=gemini_api_key)

def run_chatbot(user_input: str, memory_st, user_name: str, last_sql: str = "", last_preview: list = []):

    logger.info(f"[USER INPUT] ({user_name}) {user_input}")

    memory_st.append({"role": "user", "content": user_input})

    preview_block = "\n".join(str(row) for row in last_preview[:3]) if last_preview else ""

    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash",
    )

    agentics = agents.GeminiAgents(model=model,doc=description,user_name=user_name)

    intention = agentics.classify_intent(user_input=user_input,last_summary=preview_block, last_sql=last_sql)

    logger.info(f"[AGENTE_CLASSIFIER]: {intention}")

    preview_rows = []
    summary_response = ""
    generated_sql = None

    if intention in ["analysis-request","correction-request"]:
        
        schema_choose = agentics.schema_chooser(user_input=user_input,schema_dir=schema_path)
        schema = schema_choose.get("schema","")

        generated_sql = agentics.query_builder(intent=intention,user_input=user_input,schema=schema,last_summary=preview_block,last_sql=last_sql)
        exec = aitools.run_query(generated_sql,bq_creds)
        preview_rows = exec.get("data_preview", [])
        table_view = "\n".join(str(row) for row in preview_rows)

        summary_response = agentics.final_response_builder(table=table_view,user_input=user_input,sql=generated_sql,last_summary=preview_block)
        
        logger.info(f"[SCHEMA CHOOSER AGENT]: {schema_choose.get("type","")}")
        logger.info(f"[SQL AGENT]: {generated_sql}")
        logger.info(f"[FINAL RESPONSE AGENT]: {summary_response}")
    else:
        summary_response = agentics.general_response_builder(intent=intention,user_input=user_input,last_summary=preview_block,last_sql=last_sql)
        logger.info(f"[GENERAL RESPONSE AGENT]: {summary_response}")
    return {
        "sql": generated_sql,
        "preview": preview_rows,
        "summary": summary_response
    }

#%%