#%%

from functions import aitools, utils
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


def run_chatbot(user_input: str, memory_st, user_name:str):

    logger.info(f"[USER INPUT] ({user_name}) {user_input}")

    memory_st.append({"role": "user", "content": user_input})

    # Load API key
    creds_folder = r'C:\Users\guilherme.luz.NETSHOES\Desktop\codes\Credentials'
    gemini_path = utils.get_credentials(creds_folder, "GEMINI")
    bq_creds = utils.get_credentials(creds_folder, "BQ")

    # Load Schema
    schema_path = r"data/context/full_stock_table_doc.md"
    schema = aitools.get_schema(schema_path)

    with open(gemini_path, 'r') as f:
        gemini_api_key = f.read().strip()

    genai.configure(api_key=gemini_api_key)

    # Create model with tool (function calling)
    model = genai.GenerativeModel(
        model_name="models/gemini-1.5-flash",
        tools=[
            aitools.generate_query,
            aitools.execute_query]
    )

    tool_router = {
        "generate_query": partial(aitools.build_query,schema_text=schema),
        "execute_query": aitools.run_query
    }

    chat_block = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in memory_st[-4:]])

    system_instructions = (
        "You are a Data Expert that helps users by building SQL-based analyses using BigQuery.\n"
        "You have access to specialized tools that understand internal documentation about stock data.\n"
        f"Here's your documentation:\n {schema}\n"
        "Your job is to identify whether the user's question is a data analysis request.\n\n"
        "If it is:\n"
        "- You MUST call the tool generate_query, even if the user prompt is vague.\n"
        "- The tool has full access to all relevant schema and inventory column names.\n"
        "- You should **not ask the user for schema details** — use the tools.\n\n"
        "If the request is unrelated to data analysis, you may politely explain why you can't help right now.\n"
        "Try to orient the user of HOW you can help and WHAT you are, always being polite.\n"
        "Use everything you can to address user's needs."
    )

    system_instructions = system_instructions + chat_block

    prompt = system_instructions + "\n__USER INPUT__\n" + user_input

    response = model.generate_content(prompt)

    generated_sql = None
    preview_rows = []
    summary_response = ""

    for part in response.candidates[0].content.parts:
        if hasattr(part, "function_call") and part.function_call:
            func_name = part.function_call.name
            func_args = dict(part.function_call.args)

            logger.info(f"[TOOL CALL] Gemini triggered: {func_name} with args: {func_args}")

            # Step 1: Generate SQL
            if func_name == "generate_query":
                try:
                    result = tool_router["generate_query"](**func_args)
                    generated_sql = result.get("query").strip()

                    logger.info(f"[SQL GENERATED] {generated_sql}")


                    # Step 2: Execute the query immediately
                    try:
                        exec_result = tool_router["execute_query"](query=generated_sql, creds=bq_creds)
                        preview_rows = exec_result.get("data_preview", [])

                        logger.info(f"[QUERY RESULT] Preview: {preview_rows[:2]}")

                        # Step 3: Let Gemini respond using the previewed data
                        if preview_rows:
                            # Compose a friendly message + data
                            table_view = "\n".join(str(row) for row in preview_rows)

                            summary_prompt = (
                            "Você acabou de ajudar um usuário a analisar o que ele precisava. Aqui está a prévia do resultado:\n"
                            f"{table_view}\n\n"
                            "Agora responda ao usuário de forma útil e natural, reconhecendo o objetivo da análise "
                            "e resumindo brevemente o que a prévia contém."
                            "Sempre responda em PT-BR."

                            )

                            summary = model.generate_content(summary_prompt)
                            summary_response = summary.text.strip()
                            logger.info(f"[SUMMARY RESPONSE] {summary_response}")

                    except Exception as e:
                        summary_prompt = (
                            "Você não conseguiu executar a query gerada no BigQuery."
                            "Analise o erro apresentado e o schema existente na sua documentação."
                            f"*SCHEMA*:\n{schema}\n"
                            f"*ERRO*:\n{e}\n"
                            "Responda educadamente o erro, se o erro foi na sua query, peça para o usuário refazer a solicitação."
                            "Se o erro foi na pergunta do usuário, explique onde está errado, e educadamente oriente o usuário a realizar o pedido corretamente."
                            "Sempre responda em PT-BR."
                            )

                        summary = model.generate_content(summary_prompt)
                        summary_response = summary.text.strip()
                        
                        logger.exception(f"❌ Error generating query: {e}")
                        logger.info(f"❌ [SUMMARY RESPONSE] - Tool error: {summary_response}")
                    

                except Exception as e:
                    summary_prompt = (
                        "Você não conseguiu gerar uma query que satisfaça o pedido do usuário."
                        "Analise a documentação do schema e explique ao usuário o porquê de o pedido dele não ser possível."
                        f"*SCHEMA*:\n{schema}\n"
                        "Responda educadamente, dê sugestões de melhorias no pedido."
                        "Sempre responda em PT-BR."
                        )
                    summary = model.generate_content(summary_prompt)
                    summary_response = summary.text.strip()
                    
                    logger.exception(f"❌ Error generating query: {e}")
                    logger.info(f"❌ [SUMMARY RESPONSE] - Tool error: {summary_response}")

        else:

            summary_prompt = (
                "Você é um Especialista de Dados e está ajudando o usuário a realizar análises."
                "Você decidiu por não utilizar suas ferramentas para ajudar o usuário."
                "Entenda se sua decisão foi porque a pergunta não é relacionada a análise ou porquê a analisa solicitada não pode ser atendida.\n"
                "**SE A PERGUNTA FOR UMA ANÁLISE, PORÉM NÃO PODE SER ATENDIDA:**\n"
                "Analise a documentação do schema e explique ao usuário o porquê de o pedido dele não ser possível."
                f"*SCHEMA*:\n{schema}\n"
                f"*SUA DECISÃO*:\n{part.text.strip()}\n"
                "Responda educadamente, dê sugestões de melhorias no pedido.\n"
                "**SE O USUÁRIO NÃO ESTIVER FALANDO SOBRE ANÁLISES DE DADOS:**\n"
                "- Seja amigável e responda QUEM é você e QUAL o seu propósito.\n"
                "- Oriente o usuário a se abster apenas ao tema de análise de dados.\n"
                "**REGRAS:**\n"
                "Sempre responda em PT-BR."
            )
            summary = model.generate_content(summary_prompt)
            summary_response = summary.text.strip()

            logger.info(f"[SUMMARY RESPONSE] - No tools: {summary_response}")
        
    memory_st.append({"role": "assistant", "content": summary_response})

    return {
        "sql":generated_sql,
        "preview": preview_rows,
        "summary":summary_response
    }


#%%