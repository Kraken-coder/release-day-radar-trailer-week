import json
import os
import sys
from pathlib import Path

import pandas as pd
from pyspark.sql import SparkSession, Window, functions as F
from pyspark.ml.feature import StopWordsRemover

DATA = Path(__file__).resolve().parents[1] / "data"
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
os.environ["PYSPARK_PYTHON"] = sys.executable
spark = (SparkSession.builder.master("local[2]").appName("ReleaseDayRadar")
         .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "4")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

imdb = spark.read.option("header", True).option("multiLine", True).option("escape", '"').csv(str(DATA / "imdb.csv.gz"))
comments = spark.read.option("header", True).option("multiLine", True).option("escape", '"').csv(str(DATA / "clean/comments.csv.gz"))
text = imdb.select(F.lit("__imdb__").alias("film_id"), "text").unionByName(
    comments.select("film_id", F.col("text_clean").alias("text")))
text = text.withColumn("clean", F.trim(F.regexp_replace(
    F.lower(F.regexp_replace("text", r"<[^>]+>|https?://\S+|@[\w.-]+", " ")),
    r"[^\p{L}\s]", " ")))
text = text.withColumn("characters", F.length("clean")).withColumn(
    "words", F.when(F.col("clean") == "", 0).otherwise(F.size(F.split("clean", r"\s+"))))
text.cache()
rows = text.count()
assert rows >= 50000
summary = text.groupBy("film_id").agg(F.count("*").alias("rows"),
    F.avg("characters").alias("mean_characters"), F.avg("words").alias("mean_words"))
terms = text.select("film_id", F.explode(F.split("clean", r"\s+")).alias("term"))
terms = terms.filter((F.length("term") >= 3) & ~F.col("term").isin(StopWordsRemover.loadDefaultStopWords("english")))
terms = terms.groupBy("film_id", "term").count()
rank = Window.partitionBy("film_id").orderBy(F.desc("count"), "term")
terms = terms.withColumn("rank", F.row_number().over(rank)).filter("rank <= 20")
pd.DataFrame(summary.orderBy("film_id").collect(), columns=summary.columns).to_csv(DATA / "results/spark_summary.csv", index=False)
pd.DataFrame(terms.orderBy("film_id", "rank").collect(), columns=terms.columns).to_csv(DATA / "results/spark_terms.csv", index=False)
(DATA / "results/spark_run.json").write_text(json.dumps({"rows_processed": rows, "spark_version": spark.version}))
spark.stop()
