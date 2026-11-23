import json
import os
import tarfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
load_dotenv(ROOT / ".env")
KEY = os.environ["YOUTUBE_API_KEY"]


def collect_film(film):
    client = requests.Session()
    client.headers["User-Agent"] = "ReleaseDayRadar/1.0 (academic trailer engagement study)"
    folder = RAW / film["film_id"]
    folder.mkdir(exist_ok=True)
    for name, url in [("wikipedia.html", film["wikipedia_url"]), ("box_office.html", film["box_office_url"])]:
        if not (folder / name).exists():
            response = client.get(url, timeout=60)
            response.raise_for_status()
            (folder / name).write_bytes(response.content)
    video_file = folder / "video.json"
    if not video_file.exists():
        response = client.get("https://www.googleapis.com/youtube/v3/videos",
            params={"part": "snippet,statistics", "id": film["video_id"]},
            headers={"x-goog-api-key": KEY}, timeout=60)
        response.raise_for_status()
        video_file.write_text(response.text)
    video = json.loads(video_file.read_text())["items"][0]
    assert video["snippet"]["channelTitle"].strip() == film["channel"].strip()
    release = pd.Timestamp(film["release_date"], tz="Asia/Kolkata").tz_convert("UTC")
    if pd.Timestamp(video["snippet"]["publishedAt"]) + pd.Timedelta(days=7) > release:
        return
    state_file = folder / "collection_state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"pages": 0, "complete": False}
    while not state["complete"] and state["pages"] < 1000:
        params = {"part": "snippet", "videoId": film["video_id"], "maxResults": 100,
                  "order": "time", "textFormat": "plainText"}
        if state.get("next_page_token"):
            params["pageToken"] = state["next_page_token"]
        response = client.get("https://www.googleapis.com/youtube/v3/commentThreads",
            params=params, headers={"x-goog-api-key": KEY}, timeout=60)
        if response.status_code == 400:
            state["error"] = response.json()["error"]["message"]
            state_file.write_text(json.dumps(state))
            return
        response.raise_for_status()
        page = response.json()
        with (folder / "comments.jsonl").open("a") as file:
            for item in page["items"]:
                comment = item["snippet"]["topLevelComment"]
                snippet = comment["snippet"]
                file.write(json.dumps({"comment_id": comment["id"], "text": snippet["textOriginal"],
                    "published_at": snippet["publishedAt"], "updated_at": snippet["updatedAt"]}, ensure_ascii=False) + "\n")
        state = {"pages": state["pages"] + 1, "complete": "nextPageToken" not in page,
                 "next_page_token": page.get("nextPageToken"),
                 "collected_at": datetime.now(timezone.utc).isoformat()}
        state_file.write_text(json.dumps(state))


def collect_imdb():
    if (DATA / "imdb.csv.gz").exists():
        return
    archive = RAW / "aclImdb_v1.tar.gz"
    if not archive.exists():
        response = requests.get("https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz", stream=True, timeout=120)
        response.raise_for_status()
        with archive.open("wb") as file:
            for chunk in response.iter_content(1024 * 1024):
                file.write(chunk)
    rows = []
    with tarfile.open(archive) as corpus:
        for member in corpus:
            parts = member.name.split("/")
            if len(parts) == 4 and parts[1] in ["train", "test"] and parts[2] in ["pos", "neg"]:
                rows.append({"review_id": member.name, "split": parts[1], "label": int(parts[2] == "pos"),
                             "text": corpus.extractfile(member).read().decode("utf-8")})
            if member.name == "aclImdb/README":
                (RAW / "imdb_README.txt").write_bytes(corpus.extractfile(member).read())
    assert len(rows) == 50000
    pd.DataFrame(rows).to_csv(DATA / "imdb.csv.gz", index=False, compression="gzip")


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(collect_film, pd.read_csv(DATA / "films.csv").to_dict("records")))
    collect_imdb()
