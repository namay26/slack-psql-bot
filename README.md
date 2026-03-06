# Slack AI Data Bot MVP

A minimal Slack bot that converts natural-language questions into SQL using **LangChain + OpenAI**, executes them on **PostgreSQL**, and replies with formatted results.

## Architecture

```
User ──► /ask-data "question"
            │
            ▼
     nl_to_sql.py  (LangChain + GPT-4o-mini)
            │  generates SELECT statement
            ▼
        db.py  (psycopg2 → PostgreSQL)
            │  returns columns + rows
            ▼
        app.py  (Slack Bolt – Socket Mode)
            │  formats table, optional chart
            ▼
      Slack reply with results
```

## Prerequisites

- Python 3.11
- PostgreSQL local client
- A Slack app configured with **Socket Mode** enabled

## Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app.
2. Enable **Socket Mode**
3. Under **Slash Commands**, create:
   - `/ask-data` — "Ask a question about the data"
   - `/export-csv` — "Export last query result as CSV"
4. Under **OAuth & Permissions**, add these scopes:
   - `commands`
   - `chat:write`
   - `files:write`
5. Install the app to your workspace and copy the **Bot User OAuth Token**.
6. Fill in `.env` with your tokens.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

psql -U postgres -f db_setup.sql

python app.py
```

## Usage

In any Slack channel where the bot is invited:

```
/ask-data show revenue by region for 2025-09-01
/export-csv
```

## Prorject Structure

app.py - Entry point for the Slack bot. Handles slash commands and formats the responses that get sent back to Slack.  
nl_to_sql.py - Takes a user’s natural language query and converts it into SQL using a LangChain prompt.  
db.py - DB connection to the Postgres SQL client.    
db_setup.sql - SQL script used to create the tables and populate them with some initial sample data.  
