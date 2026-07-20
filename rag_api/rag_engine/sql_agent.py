import os
import duckdb
import pandas as pd
from typing import Union
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Why: Imports the OpenAI connection adapter and formatted prompts from within our package namespace.
from rag_engine.llm_engine import LLMEngine
from rag_engine.prompts import SYSTEM_PROMPT, REPORT_PROMPT, FIX_PROMPT

# Why: Loads environment configurations (e.g. database path credentials).
load_dotenv()

class SQLAgent:
    """
    The Orchestrator.
    Translates user questions to DuckDB SQL, executes queries with self-correction, and formats metrics.
    """
    def __init__(self):
        # Why: Set local file-system database path.
        # Connectivity: Inherits DB_PATH from docker-compose volume mounts.
        self.db_path = os.getenv("DB_PATH", "/app/data/transactions.duckdb")
        
        if not self.db_path:
            raise ValueError("❌ DB_PATH not found in environment configurations!")

        # Why: Initializes our OpenAI client wrapper.
        self.engine = LLMEngine()
        
        # Why: Store executed SQL query as state for parent API tracing logs.
        self.last_sql = "No SQL generated"
        
        # Why: Prompt template mapping user query and thread history to schema instructions.
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{question}")
        ])
        
        # Connectivity: Chains the prompt inputs into the LangChain OpenAI instance.
        self.chain = self.prompt_template | self.engine.llm
        
        # Connectivity: Chains report and fix instructions into the LLM instances.
        self.report_prompt_template = ChatPromptTemplate.from_template(REPORT_PROMPT)
        self.report_chain = self.report_prompt_template | self.engine.llm
        
        self.fix_prompt_template = ChatPromptTemplate.from_template(FIX_PROMPT)
        self.fix_chain = self.fix_prompt_template | self.engine.llm

    def generate_sql(self, question: str, chat_history: list = None) -> str:
        """
        Calls OpenAI to translate natural language into a DuckDB SQL statement.
        """
        if chat_history is None:
            chat_history = []
        try:
            response = self.chain.invoke({
                "question": question,
                "chat_history": chat_history
            })
            return response.content.strip()
        except Exception as e:
            return f"❌ SQL Generation Error: {str(e)}"

    def run_sql(self, sql: str) -> Union[pd.DataFrame, str]:
        """
        Executes the generated SQL query against the local DuckDB volume database.
        """
        if "❌" in sql:
            return sql
            
        try:
            # Why: Ensures file read connections open/close cleanly preventing database locks.
            with duckdb.connect(self.db_path) as con:
                results_df = con.execute(sql).df()
                return results_df
        except Exception as e:
            return f"❌ Database Execution Error: {str(e)}"

    def fix_sql(self, question: str, broken_sql: str, error_msg: str) -> str:
        """
        Self-Correction: Submits broken SQL and DB errors back to the LLM to fix syntax issues.
        """
        try:
            response = self.fix_chain.invoke({
                "question": question,
                "broken_sql": broken_sql,
                "error_message": error_msg
            })
            return response.content.strip()
        except Exception as e:
            return f"❌ Fix Generation Error: {str(e)}"

    def ask(self, question: str, chat_history: list = None, max_retries: int = 3) -> tuple:
        """
        Main execution loop: Question -> SQL Gen -> Query Exec (with self-correct) -> Format response.
        """
        # Step 1: Translate Question to SQL
        sql = self.generate_sql(question, chat_history)
        results_df = None
        
        # Step 2: Query Execution with Self-Correction Retry Loops
        for attempt in range(max_retries):
            # Why: Save latest SQL string representation as agent state.
            self.last_sql = sql
            
            results_df = self.run_sql(sql)
            
            # Why: If returned result is a valid pandas DataFrame, database query was successful.
            if isinstance(results_df, pd.DataFrame):
                break
                
            # Why: If execution failed, feed error back to LLM to correct.
            if attempt < max_retries - 1:
                sql = self.fix_sql(question, sql, results_df)
            else:
                return f"Sorry, I couldn't run a valid database query after {max_retries} attempts.", None
        
        # Step 3: Format query output into short investment brief
        try:
            results_str = results_df.to_markdown() if not results_df.empty else "No results found."
            response = self.report_chain.invoke({
                "question": question,
                "sql": sql,
                "results": results_str
            })
            return response.content.strip(), results_df
        except Exception as e:
            return f"❌ Reporting Error: {str(e)}", None
