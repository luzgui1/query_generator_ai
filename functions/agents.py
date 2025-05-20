from google.generativeai.types import FunctionDeclaration
from google.generativeai import GenerativeModel
from google.cloud import bigquery
import google.generativeai as genai
import pandas as pd
import logging


class GeminiAgents():

    def __init__(self,model,schema,user_name):
        """
        Inicialização de multi-agentes.
        """

        self.model = model
        self.schema = schema
        self.user_name = user_name
        self.logger = logging.getLogger("GeminiAssistant")
        self.intent = ""
    
    def classify_intent(self, user_input: str, last_summary="", last_sql=""):

        """
        Agente responsável pela classificação da intenção do usuário
        - user_input: input do usuário no front-end
        - last_summary: última resposta trazida pelo próprio agente (memória)
        - last_sql: Última query gerada pelo agente (memória)
        """

        prompt = f"""
        Você é um agente dentro de uma rede de agentes de análises de dados.
        Seu papel é classificar a intenção (objetivo) do pedido do usuário.
        Classifique a intenção nas seguintes categorias:
        - "analysis-request"
        - "correction-request"
        - "explanation-request"
        - "question"
        - "non-related"

        Retorne APENAS a categoria. Nada mais.

        Contexto:
        Última query gerada por você (se existir): {last_sql}
        Última resposta gerada por você (se existir): {last_summary}

        Input do usuário: {user_input}
        """

        self.intent = self.model.generate_content(prompt)

        return self.intent.text.strip().lower()

    
    def query_builder(self,intent:str,user_input: str, schema:str, last_summary="", last_sql=""):
        """
        Agente responsável pela geração e correção de queries
        """

        if intent == "analysis-request":
            prompt = f"""
            Você é um agente gerador de queries no Google BigQuery.
            Levando em consideração a documentação do schema apresentado e também o user_input, gere uma query que atenda à necessidade do usuário.

            *SCHEMA:*
            {schema}

            *USER_INPUT:*
            {user_input}

            *SUA ÚLTIMA RESPOSTA (Se existir):*
            {last_summary}

            REGRAS IMPORTANTES:

            1. NÃO use formatação Markdown. Não utilize crases (```sql) ou qualquer tipo de anotação de linguagem.
            2. Retorne apenas o código SQL puro, começando diretamente com SELECT, sem explicações ou comentários.
            3. Não inclua nenhum texto antes ou depois da query.
            4. Nunca utilize SELECT * — sempre seja explícito nas colunas.
            """

            query = self.model.generate_content(prompt)

            return query.text.strip()
        
        elif intent == "correction-request":
            prompt = f"""
            Você é um agente gerador de queries no Google BigQuery.
            Você gerou uma query e o usuário pediu alterações.
            Utilize o schema fornecido e o user_input como orientação.
            Com base nas informações fornecidas, altere a query que você gerou anteriormente.

            *SCHEMA:*
            {schema}

            *USER_INPUT:*
            {user_input}

            *SUA ÚLTIMA RESPOSTA:*
            {last_summary}

            *SUA ÚLTIMA QUERY:*
            {last_sql}

            REGRAS IMPORTANTES:

            1. NÃO use formatação Markdown. Não utilize crases (```sql) ou qualquer tipo de anotação de linguagem.
            2. Retorne apenas o código SQL puro, começando diretamente com SELECT, sem explicações ou comentários.
            3. Não inclua nenhum texto antes ou depois da query.
            4. Nunca utilize SELECT * — sempre seja explícito nas colunas.
            """

            query = self.model.generate_content(prompt)

            return query.text.strip()
    
    def general_response_builder(self,intent: str,user_input: str, schema:str,last_summary="", last_sql=""):

        """
        Agentes responsáveis por lidar com questões não-relacionadas à análises trazidas pelo usuário.
        """
        
        if intent == 'non-related':
            
            prompt = f"""
            Você é o agente final entre uma cadeia de agentes de geração de queries no Google BigQuery.
            O usuário não está falando sobre tópicos relacionados a análises de dados.

            **O USUÁRIO PERGUNTOU:**
            {user_input}

            Responda educadamente sobre o que o usuário perguntou, e seja persuasivo para que ele se atenha ao seu objetivo: responder dúvidas analíticas sobre a Netshoes.
            """

            response = self.model.generate_content(prompt)

            return response.text.strip()
        
        elif intent in ['explanation-request','question']:

            prompt = f"""
            Você é o agente final entre uma cadeia de agentes de geração de queries no Google BigQuery.
            O usuário está com dúvidas acerca de algum tópico relacionado OU à sua consulta anterior OU à algum detalhe da sua documentação.

            **USER_INPUT:**
            {user_input}

            **SUA ÚLTIMA RESPOSTA (SE EXISTIR):**
            {last_summary}

            **SUA ÚLTIMA QUERY (SE EXISTIR):**
            {last_sql}

            **DOCUMENTAÇÃO E SCHEMA DE DADOS:**
            {schema}


            Com base na dúvida do usuário e no histórico da conversa, responda acerca da dúvida que o usuário tenha. Sempre com educação.
            Responda como um especialista de dados.
            """
            response = self.model.generate_content(prompt)

            return response.text.strip()
        
        else:
            pass

    
    def final_response_builder(self,table:str,user_input: str, sql:str, last_summary=""):
        prompt = f"""
        Você é o agente final entre uma cadeia de agentes de geração de queries no Google BigQuery.
        Você já gerou uma query bem sucedida, e aqui estão as primeiras 10 linhas do resultado.

        {table}

        Gere uma explicação plausível para os resultados apresentados, considerando o user_input e suas conversas anteriores.

        *USER INPUT:*
        {user_input}

        *SUA ÚLTIMA RESPOSTA (Se aplicável):*
        {last_summary}

        *SQL GERADO POR VOCÊ PARA A TABELA:*
        {sql}

        *REGRAS:*
        - Seja sempre educado, solícito, traga insight para futuras análises.
        - Nunca mostre dados fictícios, apenas o que foi apresentado na tabela.
        - Se a tabela estiver vazia, explique que pode ser que tenha ocorrido um erro com a sua query.
        - Explique conceitos gerais da sua query. 
            Ex: Entendi que você pediu uma análise de estoque no dia de hoje. Por isso agreguei a soma de estoque_saldo em CURRENT_DATE().
            - Mas não há a necessidade de explicar cada sintaxe do SQL. Ex: não precisa explicar o que é um GROUP BY.
        - Seja direto ao ponto, apesar de educado. Ex: Entendi sua pergunta (X). Tomei as seguintes decisões (Y). Aqui está sua análise (Z). Sugiro estes próximos passos (W).
        """

        response = self.model.generate_content(prompt)

        return response.text.strip()


