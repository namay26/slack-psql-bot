import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from db import TABLE_SCHEMA

load_dotenv()

_llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0,
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
)

_SYSTEM_PROMPT = f"""You are a SQL expert. You have access to a PostgreSQL database with the following schema:

{TABLE_SCHEMA}

Rules:
1. Output ONLY a single valid SELECT statement – nothing else (no markdown, no explanation).
2. Never modify data (no INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE).
3. Use standard PostgreSQL syntax.
4. If the user's question cannot be answered from this table, return:
   SELECT 'Sorry, I cannot answer that from the available data.' AS message;
"""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
)

_chain = _prompt | _llm


def nl_to_sql(question: str) -> str:
    response = _chain.invoke({"question": question})
    # Strip the reply from any markdown formatting or extra text, we only need raw SQL stuff from the reply. 
    sql = response.content.strip()
    if sql.startswith("```"):
        sql = sql.split("\n", 1)[1] if "\n" in sql else sql[3:]
    if sql.endswith("```"):
        sql = sql[: -3].rstrip()
    if sql.lower().startswith("sql"):
        sql = sql[3:].strip()
    return sql
