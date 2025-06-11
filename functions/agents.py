# from google.generativeai.types import FunctionDeclaration
# from google.generativeai import GenerativeModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from google.cloud import bigquery
import google.generativeai as genai
import pandas as pd
import os
import logging


class GeminiAgents():

    def __init__(self,doc,user_name,model_name = "gemini-2.0-flash", temperature=0.2):
        """
        Inicialização de multi-agentes.
        """
        if not os.environ.get("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        self.model_name = model_name
        self.temperature = temperature
        self.model = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    temperature=self.temperature,
                    max_tokens=None,
                    timeout=None,
                    max_retries=2,
                )
        
        self.doc = doc
        self.user_name = user_name
        self.logger = logging.getLogger("GeminiAssistant")
    
    def update_model_settings(self, model_name=None, temperature=None):
        """
        Update the model settings and reinitialize the language model.
        """
        if model_name:
            self.model_name = model_name
        if temperature is not None:
            self.temperature = temperature
            
        self.model = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
    
    def classify_intent(self, user_input: str, memory):

        """

        Agente responsável pela classificação da intenção do usuário
        *Params:*

            - user_input: input do usuário no front-end
        """

        self.update_model_settings(model_name="gemini-2.0-flash", temperature=0.2)

        prompt = ChatPromptTemplate.from_messages([("system","""

            Você é um agente dentro de uma rede de agentes de análises de dados.
            Seu papel é classificar a intenção (objetivo) do pedido do usuário.
            Classifique a intenção nas seguintes categorias:
            - "analysis-request"
            - "correction-request"
            - "include_schema"
            - "explanation-request"
            - "question"
            - "non-related"

            _____________________
            Exemplos:
            - Usuário: "Preciso que realizar uma análise de estoque total do dia de ontem"
            - Resultado: "analysis-request"

            - Usuário: "Na análise anterior, preciso que você altere para que seja uma análise agregada total, e não quebrada por sku"
            - Resultado: "correction-request"

            - Usuário: "Não entendi o resultado apresentado"
            - Resultado: "explanation-request"

            - Usuário: "Poderia me falar mais acerca das variáveis existentes na tabela de estoque?"
            - Resultado: "question"

            - Usuário: "tô com fome"
            - Resultado: "non-related"
                                                    
            - Usuário: "Na análise anterior, preciso que você inclua um campo de departamentos para que eu possa filtrar skus específicos.
            - Resultado: "include_schema"
            _____________________

            Retorne APENAS a categoria. Nada mais.
            Utilize as últimas mensagens trocadas entre vocês para tomada de decisão: 
            {history}

            """),
        ("user","{user_message}")
        ])

        chain = prompt | self.model

        response = chain.invoke({"user_message":user_input, "history":memory}).content

        intent = str(response).strip().strip('"').strip("'")

        self.logger.info(f"[AGENT_INTENT_CLASSIFIER]: {intent}")

        return intent
    
    def summarize_memory(self, user_input: str, memory: list, schema: str):
        """
        Agente responsável pela leitura da memória da conversa com o usuário.
        *Params*
            - user_input: query do usuário
            - memory: memória da conversa com o usuário
        """

        self.update_model_settings(model_name="gemini-2.0-flash", temperature=0.7)

        prompt = ChatPromptTemplate.from_messages([("system","""

        Você é um agente especialista de dados.
        Seu papel é resumir sua conversa com o usuário para dar instruções para o agente seguinte.
        Com base na pergunta do usuário e no histórico da conversa, explique para o agente seguinte, a instrução que ele deve seguir para melhor atender ao usuário.
        Seja explícito quanto aos passos que o próximo agente precisa realizar para completar a instrução.
                                                    
        Esse é o histórico da conversa:

        {history}
                                                    
        Esse é o schema de dados quando necessário:
                                                    
        {doc}

        *Você deve direcionar o próximo agente com POUCAS palavras.*

        """),
        ("user","{user_message}")
        ])

        chain = prompt | self.model

        response = chain.invoke({"user_message":user_input, "history":memory,"doc":schema}).content

        summarize_memory = str(response).strip().strip('"').strip("'")

        self.logger.info(f"[AGENT_SUMMARYZE_MEMORY]: {summarize_memory}")

        return summarize_memory
        
    
    def schema_chooser(self,user_input: str,schema_dir: str, memory:list=[]):
        """
        Agente responsável pela escolha do schema que será acessado.
        """

        self.update_model_settings(model_name="gemini-2.0-flash", temperature=0.2)

        prompt = ChatPromptTemplate.from_messages([("system","""

        Seu papel é identificar se o pedido de análise do usuário é relacionado a essas opções:

            - revenue
            - stock
            - none
        
        Com base no input do usuário, siga as seguintes regras:
        
            Se relacionado a receita -> revenue
            Se relacionado a estoque -> stock
            Se relacionado a receita E estoque -> revenue,stock
            Se não tiver relação com nenhuma das opções acima -> none

        Retorne APENAS alguma das opções acima.
                                                    
        Use o histórico abaixo se necessário:
        {history}
        """),
        ("user","{user_message}")
        ]
        )

        chain = prompt | self.model

        response = chain.invoke({"user_message":user_input,"history":memory}).content
        raw_types = str(response).strip().strip('"').strip("'")

        if raw_types == "none":
            chosen = []
        else:
            chosen = [t.strip() for t in raw_types.split(",") if t.strip()]
        
        schemas = {}
        for t in chosen:
            md_path =  f"{schema_dir}\{t}.md"
            try:
                with open(md_path,"r",encoding='utf-8') as d:
                    schemas[t] = d.read()
            except FileNotFoundError:
                schemas[t] = f"**Erro:** arquivo {md_path} não encontrado."

        document = "\n\n".join(schemas[t] for t in chosen)


        self.logger.info(f"[AGENT_SCHEMA_CHOOSER]: 'type':{chosen},'document':{md_path}")

        return {"type":chosen,"schema":document}
    
    def query_builder(self,intent:str,user_input: str, schema:list=[],memory: list=[]):
        """
        Agente responsável pela geração e correção de queries
        """

        self.update_model_settings(model_name="gemini-2.0-flash", temperature=0.7)

        if intent == "analysis-request":
            prompt = ChatPromptTemplate.from_messages([("system","""
                Você é um agente gerador de queries no Google BigQuery.
                Levando em consideração a documentação do schema apresentado e também o user_input, gere uma query que atenda à necessidade do usuário.

                *DOCUMENTAÇÃO GERAL:*
                {doc}

                *SCHEMA:*
                {doc_schema}

                REGRAS IMPORTANTES:

                1. NÃO use formatação Markdown. Não utilize crases (```sql) ou qualquer tipo de anotação de linguagem.
                2. Retorne apenas o código SQL puro, começando diretamente com SELECT, sem explicações ou comentários.
                3. Não inclua nenhum texto antes ou depois da query.
                4. Nunca utilize SELECT * — sempre seja explícito nas colunas.
                5. Sempre use a primary key da documentação como foco dos agrupamentos.
            """),
            ("user","{user_message}")
            
            ])

            chain = prompt | self.model

            schemas_text = "\n\n".join(
                                f"Schema {i+1}:\n{schema}"
                                for i, schema in enumerate(schema)
                            )

            response = chain.invoke({"user_message":user_input,"doc":self.doc,"doc_schema":schemas_text}).content

            query = str(response).strip().strip('"').strip("'").strip(" ```sql").strip('```')
            self.logger.info(f"[AGENT_QUERY_BUILDER]: {query}")

            return query
        
        elif intent == "include_schema":

            prompt = ChatPromptTemplate.from_messages([("system","""
                Você é um agente gerador de queries no Google BigQuery.
                Você gerou uma query e o usuário pediu inclusão de mais dados.
                Utilize o schema fornecido e o user_input como orientação.
                Com base nas seguintes informações fornecidas, altere a query que você gerou anteriormente.

                *SUA MEMÓRIA:*
                    {history}
                
                *SCHEMA:*
                    {doc_schema}

                REGRAS IMPORTANTES:

                1. NÃO use formatação Markdown. Não utilize crases (```sql) ou qualquer tipo de anotação de linguagem.
                2. Retorne apenas o código SQL puro, começando diretamente com SELECT, sem explicações ou comentários.
                3. Não inclua nenhum texto antes ou depois da query.
                4. Nunca utilize SELECT * — sempre seja explícito nas colunas.
                5. Sempre use a primary key da documentação como foco dos agrupamentos.
            """),
            ("user","{user_message}")
            ])

            chain = prompt | self.model

            schemas_text = "\n\n".join(
                                f"Schema {i+1}:\n{schema}"
                                for i, schema in enumerate(schema)
                            )

            response = chain.invoke({"user_message":user_input,"history":memory,"doc_schema":schemas_text}).content

            query = str(response).strip().strip('"').strip("'").strip(" ```sql").strip('```')

            self.logger.info(f"[AGENT_QUERY_BUILDER]: {query}")

            return query

        elif intent == "correction-request":

            prompt = ChatPromptTemplate.from_messages([("system","""
                Você é um agente gerador de queries no Google BigQuery.
                Você gerou uma query e o usuário pediu alterações.
                Utilize o schema fornecido e o user_input como orientação.
                Com base nas seguintes informações fornecidas, altere a query que você gerou anteriormente.

                *SUA MEMÓRIA:*
                    {history}
                
                *SCHEMA:*
                    {doc_schema}

                REGRAS IMPORTANTES:

                1. NÃO use formatação Markdown. Não utilize crases (```sql) ou qualquer tipo de anotação de linguagem.
                2. Retorne apenas o código SQL puro, começando diretamente com SELECT, sem explicações ou comentários.
                3. Não inclua nenhum texto antes ou depois da query.
                4. Nunca utilize SELECT * — sempre seja explícito nas colunas.
                5. Sempre use a primary key da documentação como foco dos agrupamentos.
            """),
            ("user","{user_message}")
            ])

            chain = prompt | self.model

            schemas_text = "\n\n".join(
                                f"Schema {i+1}:\n{schema}"
                                for i, schema in enumerate(schema)
                            )

            response = chain.invoke({"user_message":user_input,"history":memory,"doc_schema":schemas_text}).content

            query = str(response).strip().strip('"').strip("'").strip(" ```sql").strip('```')

            self.logger.info(f"[AGENT_QUERY_BUILDER]: {query}")

            return query
        
    def query_fixer(self,user_input: str,error: str, schema:list, memory: list=[]):

            prompt = ChatPromptTemplate.from_messages([("system","""
                Você é um agente gerador de queries no Google BigQuery.
                A query gerada anteriormente deu erro.
                Com base nas seguintes informações fornecidas, altere a query gerada anteriormente.
                Utilize o schema fornecido e o user_input como orientação.
                
                *SUA MEMÓRIA:*
                    {history}
                
                *SCHEMA:*
                    {doc_schema}

                *ERRO:*
                    {erro}

                REGRAS IMPORTANTES:

                1. NÃO use formatação Markdown. Não utilize crases (```sql) ou qualquer tipo de anotação de linguagem.
                2. Retorne apenas o código SQL puro, começando diretamente com SELECT, sem explicações ou comentários.
                3. Não inclua nenhum texto antes ou depois da query.
                4. Nunca utilize SELECT * — sempre seja explícito nas colunas.
                5. Sempre use a primary key da documentação como foco dos agrupamentos.
            """),
            ("user","{user_message}")
            ])

            chain = prompt | self.model

            schemas_text = "\n\n".join(
                                f"Schema {i+1}:\n{schema}"
                                for i, schema in enumerate(schema)
                            )

            response = chain.invoke({"user_message":user_input,"erro":error,"history":memory,"doc_schema":schemas_text}).content

            query = str(response).strip().strip('"').strip("'").strip(" ```sql").strip('```')

            self.logger.info(f"[QUERY_EXECUTION_ERROR]: {error}")

            self.logger.info(f"[AGENT_QUERY_FIXER]: {query}")

            return query


    
    def general_response_builder(self,intent: str,user_input: str,memory: list, schema:list = []):

        """
        Agentes responsáveis por lidar com questões não-relacionadas à análises trazidas pelo usuário.
        """

        self.update_model_settings(model_name="gemini-2.0-flash", temperature=0.7)
        
        if intent == 'non-related':
            
            prompt = ChatPromptTemplate.from_messages([("system","""
            Você é o agente final entre uma cadeia de agentes de geração de queries no Google BigQuery.
            O usuário não está falando sobre tópicos relacionados a análises de dados.
            Responda educadamente sobre o que o usuário perguntou, e seja persuasivo para que ele se atenha ao seu objetivo: responder dúvidas analíticas sobre a Netshoes.

            Histórico da conversa: {history}
            """),
            ("user","{user_message}")
            ])

            chain = prompt | self.model

            response = chain.invoke({"user_message":user_input,"history":memory}).content

            self.logger.info(f"[AGENT_GENERAL_RESPONSER]: {response}")

            return response.strip().strip('"').strip("'")
        
        elif intent in ['explanation-request','question']:
            if schema:
                prompt = ChatPromptTemplate.from_messages([("system","""
                Você é o agente final entre uma cadeia de agentes de geração de queries no Google BigQuery.
                O usuário está com dúvidas acerca de algum tópico.
                Utilize as seguintes informações para construir sua resposta

                **ORIENTAÇÃO DO AGENTE DE RESUMO DE MEMÓRIA:**
                {memory_agent}

                **DOCUMENTAÇÃO E SCHEMA DE DADOS:**
                    Doc:
                        {doc}
                    
                    Schema:
                        {schema}


                Com base na dúvida do usuário e no histórico da conversa, responda acerca da dúvida que o usuário tenha. Sempre com educação.
                Responda como um especialista de dados.
                """),

                ("user","{user_message}")
                ])

            else:
                prompt = ChatPromptTemplate.from_messages([("system","""
                    Você é o agente final entre uma cadeia de agentes de geração de queries no Google BigQuery.
                    O usuário está com dúvidas acerca de algum tópico.
                    Utilize as seguintes informações para construir sua resposta

                    **ORIENTAÇÃO DO AGENTE DE RESUMO DE MEMÓRIA:**
                    {memory_agent}

                    **DOCUMENTAÇÃO DE DADOS:**
                    {doc}

                    Com base na dúvida do usuário e no histórico da conversa, responda acerca da dúvida que o usuário tenha. Sempre com educação.
                    Responda como um especialista de dados.
                """),
                ("user","{user_message}")
                ])
    

            chain = prompt | self.model


            schemas_text = "\n\n".join(
                                f"Schema {i+1}:\n{schema}"
                                for i, schema in enumerate(schema)
                            )            

            response = chain.invoke({"user_message":user_input,"doc":schemas_text,"memory_agent":self.summarize_memory(user_input,memory,schemas_text)}).content

            self.logger.info(f"[AGENT_GENERAL_RESPONSER]: {response.strip().strip('"').strip("'")}")

            return response.strip().strip('"').strip("'")
        
        else:
            pass

    
    def final_response_builder(self,table:str,user_input: str,memory:dict):

        self.update_model_settings(model_name="gemini-2.0-flash", temperature=0.7)

        prompt = ChatPromptTemplate.from_messages([("system","""
            Você é o agente final entre uma cadeia de agentes de geração de queries no Google BigQuery.
            Você já gerou uma query bem sucedida, e aqui estão as primeiras 10 linhas do resultado.

            {tabela}

            Gere uma explicação plausível para os resultados apresentados, considerando o user_input e suas conversas anteriores.

            *MEMÓRIA DE SUA CONVERSA:*
            {history}

            *REGRAS:*
            - Seja sempre educado, solícito, traga insight para futuras análises.
            - Nunca mostre dados fictícios, apenas o que foi apresentado na tabela.
            - Se a tabela estiver vazia, explique que pode ser que tenha ocorrido um erro com a sua query.
            - Explique conceitos gerais da sua query. 
                Ex: Entendi que você pediu uma análise de estoque no dia de hoje. Por isso agreguei a soma de estoque_saldo em CURRENT_DATE().
                - Mas não há a necessidade de explicar cada sintaxe do SQL. Ex: não precisa explicar o que é um GROUP BY.
            - Seja direto ao ponto, apesar de educado. Ex: Entendi sua pergunta (X). Tomei as seguintes decisões (Y). Aqui está sua análise (Z). Sugiro estes próximos passos (W).
        """),
        ("user","{user_message}")
        ])

        chain = prompt | self.model

        response = chain.invoke({"user_message":user_input,"tabela":table,"history":memory}).content

        self.logger.info(f"[AGENT_FINAL_RESPONSER]: {response.strip().strip('"').strip("'")}")

        return response.strip().strip('"').strip("'")


