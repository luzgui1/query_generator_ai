import streamlit as st
from main import run_chatbot
import pandas as pd

st.set_page_config(page_title="Data Analyst Assistant", layout="wide")
st.title("📊 Assistente CUBO (Gemini-powered)")

# Step 1: Ask for username once
if "username" not in st.session_state:
    username_input = st.text_input("Seu nome de usuário:")
    if username_input:
        st.session_state.username = username_input
        st.session_state[username_input] = []
        st.session_state[f"{username_input}_sql"] = ""
        st.session_state[f"{username_input}_preview"] = []
        st.rerun() 
else:
    username = st.session_state.username
    st.markdown(f"👤 **Usuário atual:** `{username}`")

    # Step 2: User interaction
    user_input = st.text_area("Descreva seu pedido:", height=150)

    if st.button("Executar análise"):
        if user_input.strip() == "":
            st.warning("Insira seu pedido primeiro.")
        else:
            with st.spinner("Rodando a análise solicitada..."):
                result = run_chatbot(
                                user_input,
                                memory_st=st.session_state[username],
                                user_name=username,
                                last_sql=st.session_state.get(f"{username}_sql", ""),
                                last_preview=st.session_state.get(f"{username}_preview", [])
                            )

            st.session_state[f"{username}_sql"] = result.get("sql", "")
            st.session_state[f"{username}_preview"] = result.get("preview", [])

            if result.get("sql"):
                st.subheader("Gemini's SQL")
                st.code(result["sql"], language="sql")

            if result.get("preview"):
                st.subheader("📊 Amostra de dados")
                st.dataframe(pd.DataFrame(result["preview"]))

            if result.get("summary"):
                st.subheader("💬 Resposta do Agente:")
                st.write(result["summary"])
            else:
                st.info("No summary generated.")



