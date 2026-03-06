import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "dbname": os.getenv("DB_NAME", "analytics"),
}

TABLE_SCHEMA = """
Table: public.sales_daily
Columns:
  - date        (date)          – the calendar date of the record
  - region      (text)          – geographic region (e.g. North, South, East, West)
  - category    (text)          – product category (e.g. Electronics, Grocery, Fashion)
  - revenue     (numeric 12,2)  – total revenue in dollars
  - orders      (integer)       – number of orders
Primary key: (date, region, category)
""".strip()


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def execute_query(sql: str) -> tuple[list[str], list[tuple]]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            return columns, rows
    finally:
        conn.close()
