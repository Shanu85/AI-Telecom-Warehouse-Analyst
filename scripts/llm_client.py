import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from groq import Groq,RateLimitError as GroqRateLimitError
import google.generativeai as gemini
from google.generativeai.types import RequestOptions
from data.duckdb_manager import DuckDBManager
from scripts.vector_client import VectorStore
from dotenv import load_dotenv
import logging
import time
from data.schema_definitions import schema_descriptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

class GroqProvider:
    name = "Groq (llama-3.3-70b)"
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"),timeout=300)
    
    def complete(self,messages:list[dict],temperature:float=0.0,max_tokens:int=1000):
        response=self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content.strip()

class GeminiProvider:
    name = "Gemini (gemini-2.5-flash)"
    def __init__(self):
        gemini.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.client=gemini.GenerativeModel("gemini-2.5-flash")
    
    def complete(self,messages:list[dict],temperature:float=0.0,max_tokens:int=1000):
        # Gemini uses a different format

        # returns first match, and returns "" instead of crashing if there's no system message.
        system_msg=next((m['content'] for m in messages if m['role']=='system'),"") 
        user_msg=next((m['content'] for m in messages if m['role']=='user'),"")
        prompt=f"{system_msg}\n\n{user_msg}" if system_msg else user_msg

        response=self.client.generate_content(
                prompt,
                generation_config=gemini.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                ),
                request_options={"timeout": 60.0}
            )
    
        
        return response.text.strip()

class LLMFallbackChain:
    """
    Tries providers in order: Gemini → Groq
    Falls through to the next provider on rate limits or API errors.
    Raises RuntimeError only if ALL providers fail.
    """

    def __init__(self):
        self.providers = self._init_providers()
    
    def _init_providers(self) -> list:
        providers = []
        try:
            providers.append(GroqProvider())
            logger.info("✅ Groq provider initialized")
        except Exception as e:
            logger.warning(f"⚠️ Groq unavailable: {e}")

        try:
            providers.append(GeminiProvider())
            logger.info("✅ Gemini provider initialized")
        except Exception as e:
            logger.warning(f"⚠️ Gemini unavailable: {e}")
        
        if not providers:
            raise RuntimeError("No LLM providers available. Check your API keys.")

        return providers

    def complete(self,messages: list[dict], temperature: float = 0, max_tokens: int = 1000)->tuple[str, str]:
        """
        Returns (response_text, provider_name_used).
        Tries each provider in order.
        """
        last_error=None
        for provider in self.providers:
            try:
                logger.info(f"🔄 Trying provider: {provider.name}")
                result = provider.complete(messages, temperature, max_tokens)
                logger.info(f"✅ Success with: {provider.name}")
                return result, provider.name

            except GroqRateLimitError as e:
                logger.warning(f"⚡ Rate limit hit on {provider.name}, falling back...")
                last_error = e
                time.sleep(1)
            
            except Exception as e:
                logger.warning(f"❌ {provider.name} failed: {e}, falling back...")
                last_error = e
        
        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")


class LLM_Client:
    def __init__(self,model:str="llama-3.3-70b-versatile"):
        self.llm = LLMFallbackChain()
        self.last_provider_used = None
    
    def _strip_markdown(self, sql: str) -> str:
        """Remove markdown code fences the LLM sometimes adds."""
        sql = sql.strip()
        if sql.startswith("```"):
            # Remove opening fence (```sql or just ```)
            sql = sql.split("\n", 1)[-1]
        if sql.endswith("```"):
            sql = sql.rsplit("```", 1)[0]
        return sql.strip()
    
    def get_table_schemas_text(self,tables:list[str],db:DuckDBManager)->str:
        """
        Pull schema and description for selected tables from DuckDB and format as text for the LLM.
        Uses existing db.get_table_schema() method.
        """
        tables_schema=[]
        for table in tables:
            schema=db.get_table_schema(table)
            desc_map  = schema_descriptions.get(table, {})
            table_desc = desc_map.get("_table_description", "")

            lines = [f"Table: `{table}`"]
            if table_desc:
                lines.append(f"Description: {table_desc}")
            
            lines.append("Columns:")
            for col in schema:
                col_name = col["column"]
                col_type = col["type"]
                col_desc = desc_map.get(col_name, "")

                if col_desc:
                    lines.append(f"  - {col_name} ({col_type}): {col_desc}")
                else:
                    lines.append(f"  - {col_name} ({col_type})")
            
            tables_schema.append("\n".join(lines))
            
        return "\n\n".join(tables_schema)

    def generate_confidence_score(self,user_question:str,sql:str,schema_text:str):
        """
        Ask the LLM to rate its own SQL confidence.
        Returns: { "score": int (1-10), "reason": str, "warning": bool }
        """

        system_prompt = """You are an expert SQL reviewer. 
            Analyze a generated SQL query and rate its confidence.
            
            Respond in this EXACT JSON format, nothing else:
            {
                "score": <integer 1-10>,
                "reason": "<one sentence explaining the score>",
                "assumptions": ["<assumption 1>", "<assumption 2>"]
            }
            
            Scoring guide:
            - 9-10: Straightforward query, schema clearly supports it, no ambiguity
            - 7-8:  Minor assumptions made (e.g., assumed a JOIN key), likely correct
            - 5-6:  Ambiguous column names, or question could be interpreted multiple ways
            - 3-4:  Schema doesn't perfectly match the question, significant assumptions made
            - 1-2:  Schema seems wrong for this question, or query is very uncertain
        """

        user_content = f"""Schema: {schema_text} User Question: {user_question} 
        Generated SQL: {sql} Rate this SQL."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ]

        try:
            raw, provider = self.llm.complete(messages, temperature=0, max_tokens=200)
            # Strip markdown if LLM wraps in ```json
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[-1]
            if clean.endswith("```"):
                clean = clean.rsplit("```", 1)[0]

            parsed = json.loads(clean.strip())

            return {
                "score":       int(parsed.get("score", 5)),
                "reason":      parsed.get("reason", "No reason provided"),
                "assumptions": parsed.get("assumptions", []),
                "warning":     int(parsed.get("score", 5)) < 6
            }
        
        except Exception as e:
            logger.warning(f"Confidence scoring failed: {e}")
            # Fail silently — don't break the main pipeline
            return {
                "score": None,
                "reason": "Could not evaluate confidence",
                "assumptions": [],
                "warning": False
            }


    def generate_sql(self,user_question:str,schema_text:str,vector_client:VectorStore,recent_chat_history:list[dict])->str:
        """
        Ask Groq/LLaMA to convert the user's natural language question into a DuckDB SQL query.
        Uses user_question to find similar question from vector store and their SQL
        Injects last 3 Q&A turns so follow-ups like "now show same for Gujarat" resolve correctly.
        Returns only the raw SQL string.
        """

        similar_examples=vector_client.get_similar_examples(user_question)

        print(f"Similar examples from vector DB : {similar_examples}")

        # ✅ Format few-shot examples into a string block
        few_shot_text = ""
        if similar_examples:
            few_shot_text = "\n\nHere are similar questions and their correct SQL (use these as reference):\n"
            for i, ex in enumerate(similar_examples, 1):
                few_shot_text += f"\nExample {i}:\n  Q: {ex['question']}\n  SQL: {ex['sql']}\n"
            few_shot_text += "\nNow generate SQL for the new question below using these as guidance.\n"

        system_prompt = f"""You are an expert SQL engineer specializing in DuckDB.
        Given a database schema and a user question, generate a valid DuckDB SQL SELECT query.
        {few_shot_text}
        RULES — follow every rule strictly:

        1. STRING FILTERS: Always use case-insensitive comparison.
        Use LOWER(column) = LOWER('value') or column ILIKE 'value'.
        NEVER use column = 'value' directly for text/VARCHAR columns.

        2. DATE ARITHMETIC — CRITICAL: The `month` column is stored as VARCHAR (e.g. '2023-01').
        You CANNOT subtract an INTERVAL from a VARCHAR. Always cast first:
            CAST(month || '-01' AS DATE)
        
        Correct pattern for "last N months":
            WHERE CAST(month || '-01' AS DATE) >= 
                (SELECT CAST(MAX(month) || '-01' AS DATE) FROM <table>) - INTERVAL '<N> months'
        
        For sorting/comparing months as text, VARCHAR order works correctly for YYYY-MM format.
        For any INTERVAL math, ALWAYS cast to DATE first. No exceptions.

        3. OUTPUT: Return ONLY the raw SQL query — no markdown, no backticks, no explanation.

        4. SAFETY: Only use SELECT statements. Never INSERT, UPDATE, DELETE, DROP, or ALTER.

        5. SYNTAX: Use proper DuckDB syntax. Use table aliases for clarity when joining.

        6. AGGREGATION: Always include appropriate GROUP BY when using aggregate functions.

        7. RESULT SIZE: Limit results to 100 rows unless the question explicitly asks for all rows.
        """
        
        # golden rule: [system] → [history] → [current question]
        # history lets LLM resolve follow-ups like "now for Gujarat" or "filter those by penalty"
        messages = [{'role':'system','content':system_prompt}]

        #Injects only USER turns from history (not assistant answers) to prevent the LLM from hallucinating SQL values from previous text answers
        user_only_history=[m for m in recent_chat_history if m['role'] == 'user']

        if recent_chat_history:
            messages += user_only_history

        messages.append({'role':'user','content':f"Schema:\n{schema_text}\n\nQuestion: {user_question}"})

        sql,provider=self.llm.complete(messages,temperature=0)

        self.last_provider_used = provider
        
        return self._strip_markdown(sql)
    
    def generate_sql_with_retries(self,user_question:str,schema_txt:str,db:DuckDBManager,vector_client:VectorStore,recent_chat_history:list[dir],max_retries:int=2):
        """
        Generate SQL and auto-correct if DuckDB throws an error.
        Returns (sql, results_as_list_of_dicts,confidence of sql).
        """

        sql=self.generate_sql(user_question,schema_txt,vector_client,recent_chat_history)
        for attempt in range(max_retries+1):
            try:
                # Safety check: only allow SELECT
                clean_sql = self._strip_markdown(sql)  # ✅ strip fences first
                if not clean_sql.upper().startswith("SELECT"):
                    raise ValueError(f"Non-SELECT statement blocked: {clean_sql[:80]}")
                results = db.execute_query(clean_sql)

                # check confidence of results
                confidence = self.generate_confidence_score(user_question, clean_sql, schema_txt)

                return sql, results,confidence

            except Exception as e:
                if attempt==max_retries:
                    raise RuntimeError(f"SQL failed after {max_retries} retries.\nLast SQL:\n{sql}\nError: {e}")
                
                fix_prompt = f"""The following DuckDB SQL query failed with this error: Error: {e}
                    Broken SQL: {sql}, Schema: {schema_txt}, Original question: {user_question}
                    Please return a corrected SQL query. Return ONLY the raw SQL, nothing else."""
                
                messages=[
                        {"role": "system", "content": "You are an expert DuckDB SQL engineer. Fix broken SQL queries. Return ONLY raw SQL."},
                        {'role':'user','content':fix_prompt}
                    ]

                sql,provider=self.llm.complete(messages,temperature=0)

                sql = self._strip_markdown(sql)
                self.last_provider_used=provider
                continue

        return sql, results, {"score": None, "reason": "", "assumptions": [], "warning": False}
    
    def generate_answer(self,user_question:str,sql:str,results,recent_chat_history:list[dir])->str:
            """
            Ask Groq/LLaMA to interpret the SQL results and answer the user in plain English.
            """

            # for a user_question, we may have multiple rows(answer), hence Truncate results if too large to avoid token limits

            results_preview = results[:50]
            truncated = len(results) > 50

            system_prompt = """You are a helpful data analyst for a telecom company.
                    Given a user's question, the SQL query that was run, and the query results,
                    provide a clear, concise answer in plain English.
                    If this is a follow-up question, acknowledge the context naturally.

                    STRICT RULES:
                    - Answer ONLY using the data provided in the results below
                    - NEVER add disclaimers, notes, or caveats about data availability
                    - NEVER say things like 'exact results not provided' or 'this is a general representation'
                    - If results are empty, say 'No data found' and suggest why
                    - Be specific with numbers and names from the actual results
                    - Keep answer under 5 sentences"""

            user_content = f"""CURRENT QUESTION: {user_question}
            EXECUTED SQL: {sql}
            ⚠️ USE ONLY THESE RESULTS — DO NOT USE CHAT HISTORY FOR DATA:
            {json.dumps(results_preview, indent=2, default=str)}
            ({len(results)} rows total{', showing first 50' if truncated else ''})
            """

            # golden rule
            # [system] → [history turn 1] → [history turn 2] → [current question]            
            messages = [{"role": "system", "content": system_prompt}]

            # History injected BEFORE current question
            # Inject last N conversation turns so LLM understands follow-ups
            if recent_chat_history:
                messages += recent_chat_history

            # Current question with actual results goes LAST
            messages.append({"role": "user", "content": user_content})
            
            answer, provider = self.llm.complete(messages, temperature=0.3, max_tokens=500)
            self.last_provider_used = provider
            return answer

