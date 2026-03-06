import csv
import hashlib
import io
import logging
import os
from collections import OrderedDict
import matplotlib
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from tabulate import tabulate
from db import execute_query
from nl_to_sql import nl_to_sql

matplotlib.use("Agg") 

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Simple cache (LRU) for repeated questions.
_CACHE_MAX = 128
_cache: OrderedDict[str, tuple[str, list[str], list[tuple]]] = OrderedDict()


def _cache_key(question: str) -> str:
    return hashlib.sha256(question.strip().lower().encode()).hexdigest()


def _get_cached(question: str):
    key = _cache_key(question)
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]
    return None


def _set_cache(question: str, sql: str, columns: list[str], rows: list[tuple]):
    key = _cache_key(question)
    _cache[key] = (sql, columns, rows)
    if len(_cache) > _CACHE_MAX:
        _cache.popitem(last=False)

_last_query: dict[str, tuple[str, list[str], list[tuple]]] = {}

def _format_table(columns: list[str], rows: list[tuple], max_rows: int = 20) -> str:
    display_rows = rows[:max_rows]
    table = tabulate(display_rows, headers=columns, tablefmt="simple")
    if len(rows) > max_rows:
        table += f"\n… and {len(rows) - max_rows} more rows"
    return table

def _build_chart(columns: list[str], rows: list[tuple]) -> io.BytesIO | None:
    if len(columns) != 2 or len(rows) == 0:
        return None
    try:
        labels = [str(r[0]) for r in rows]
        values = [float(r[1]) for r in rows]
    except (ValueError, TypeError):
        return None

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(labels, values, color="#4A90D9")
    ax.set_ylabel(columns[1])
    ax.set_title(f"{columns[1]} by {columns[0]}")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf


def _build_csv(columns: list[str], rows: list[tuple]) -> io.BytesIO:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    writer.writerows(rows)
    csv_bytes = io.BytesIO(buf.getvalue().encode("utf-8"))
    csv_bytes.seek(0)
    return csv_bytes

@app.command("/ask-data")
def handle_ask_data(ack, command, say, client):
    ack()

    question = command.get("text", "").strip()
    channel = command["channel_id"]

    if not question:
        say("Usage: `/ask-data <your question>`\nExample: `/ask-data show revenue by region for 2025-09--01`")
        return

    say(f"Processing : _{question}_")

    cached = _get_cached(question)
    if cached:
        sql, columns, rows = cached
        logger.info("Cache hit for question : %s", question)
    else:
        try:
            sql = nl_to_sql(question)
            logger.info("Generated SQL : %s", sql)
        except Exception as exc:
            say(f"Failed to generate SQL :\n```{exc}```")
            return

        try:
            columns, rows = execute_query(sql)
        except Exception as exc:
            say(f"SQL execution error :\n```{exc}```\nGenerated SQL:\n```{sql}```")
            return

        _set_cache(question, sql, columns, rows)

    _last_query[channel] = (sql, columns, rows)

    if not rows:
        say(f"Query returned no rows.\n```{sql}```")
        return

    table_text = _format_table(columns, rows)
    reply = (
        f"*Query:* `{sql}`\n"
        f"*Rows:* {len(rows)}\n"
        f"```\n{table_text}\n```\n"
        f"_Tip: use `/export-csv` to download the full result as CSV._"
    )
    say(reply)

    chart_buf = _build_chart(columns, rows)
    if chart_buf:
        try:
            client.files_upload_v2(
                channel=channel,
                file=chart_buf,
                filename="chart.png",
                title="Result chart",
                initial_comment="Here's a quick chart of the result:",
            )
        except Exception as exc:
            logger.warning("Chart upload failed: %s", exc)
 
@app.command("/export-csv")
def handle_export_csv(ack, command, client):
    ack()
    channel = command["channel_id"]

    last = _last_query.get(channel)
    if not last:
        client.chat_postMessage(channel=channel, text="No previous query to export. Run `/ask-data` first.")
        return

    sql, columns, rows = last
    csv_buf = _build_csv(columns, rows)

    try:
        client.files_upload_v2(
            channel=channel,
            file=csv_buf,
            filename="query_result.csv",
            title="Query Result CSV",
            initial_comment=f"CSV export ({len(rows)} rows)\n`{sql}`",
        )
    except Exception as exc:
        client.chat_postMessage(channel=channel, text=f"CSV upload failed:\n```{exc}```")

if __name__ == "__main__":
    logger.info("Slack AI Data Bot starting …")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
