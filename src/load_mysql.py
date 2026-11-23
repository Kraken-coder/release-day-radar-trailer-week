import json
import os
from pathlib import Path

import pandas as pd
import pymysql
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
connection = pymysql.connect(host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "3306")), user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""), charset="utf8mb4")
cursor = connection.cursor()
for statement in (ROOT / "src/schema.sql").read_text().split(";"):
    if statement.strip():
        cursor.execute(statement)

films = pd.read_csv(ROOT / "data/clean/films.csv")
videos = pd.read_csv(ROOT / "data/clean/videos.csv").merge(pd.read_csv(ROOT / "data/results/collection_coverage.csv"), on="film_id")
daily = pd.read_csv(ROOT / "data/clean/daily_collections.csv")
comments = pd.read_csv(ROOT / "data/clean/comments.csv.gz", keep_default_na=False)
for frame, column in [(films, "release_at"), (videos, "trailer_at"), (comments, "published_at")]:
    frame[column] = pd.to_datetime(frame[column], utc=True).dt.tz_localize(None)
daily["date"] = pd.to_datetime(daily["date"]).dt.date
tables = {
    "films": films[["film_id", "title", "language", "release_at"]],
    "trailers": videos[["video_id", "film_id", "trailer_at", "history_complete"]],
    "daily_collections": daily[["film_id", "day", "date", "india_net_cr"]],
    "comments": comments[["comment_id", "film_id", "published_at", "text_clean", "in_trailer_week"]],
}
for name in ["comments", "trailers", "daily_collections", "films"]:
    cursor.execute(f"DELETE FROM {name}")
for name, frame in tables.items():
    columns = list(frame.columns)
    sql = f"INSERT INTO {name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
    cursor.executemany(sql, frame.astype(object).where(frame.notna(), None).itertuples(index=False, name=None))
connection.commit()
results = []
for statement in (ROOT / "src/queries.sql").read_text().split(";"):
    if statement.strip():
        cursor.execute(statement)
        results.append({"query": statement.strip(), "columns": [column[0] for column in cursor.description], "rows": cursor.fetchall()})
(ROOT / "data/results/sql_results.json").write_text(json.dumps(results, default=str, indent=2))
connection.close()
