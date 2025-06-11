import streamlit as st
from main import run_chatbot
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Data Analyst Assistant", layout="wide")
st.title("📊 Assistente CUBO (Gemini-powered)")

# Configuração do usuário para separação de históricos
if "username" not in st.session_state:
    username_input = st.text_input("Seu nome de usuário:")
    if username_input:
        st.session_state.username = username_input
        st.session_state.chat_history = []
        st.rerun()
    else:
        st.stop()
else:
    username = st.session_state.username
    st.markdown(f"👤 **Usuário atual:** `{username}`")

agent_result = None
user_input = st.chat_input("Descreva seu pedido:")

if user_input:
    # append user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.spinner("Rodando a análise solicitada..."):
        result = run_chatbot(
            user_input,
            chat_history =st.session_state.chat_history,
            user_name=username,
        )

    # append assistant message
    assistant_summary = result.get("summary", "Nenhuma resposta gerada.")
    assistant_query = result.get("sql","Nenhuma query gerada.")
    assistant_preview = result.get("preview","Nenhuma base de dados gerada.")

    st.session_state.chat_history.append({"role": "assistant", "content": assistant_summary,
                                           "query":assistant_query,
                                           "data_preview":assistant_preview})
    agent_result = result

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if agent_result:
    if agent_result.get("sql"):
        st.subheader("💻 Gemini's SQL")
        st.code(agent_result["sql"], language="sql")

    if agent_result.get("preview"):
        st.subheader("📊 Amostra de dados")
        st.dataframe(pd.DataFrame(agent_result["preview"]))

    # (the “assistant” message already printed summary above, so no need to repeat)

    # — expand for raw JSON
    with st.expander("🔍 Dados brutos do agente"):
        st.json(agent_result)


