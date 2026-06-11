from __future__ import annotations

from pathlib import Path
import re
import sys
import time
from statistics import mean
from typing import Any
from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
LOCAL_DEPS = PROJECT_ROOT / ".codex_pydeps"
LOCAL_NEWS_DEPS = PROJECT_ROOT / ".codex_news_deps"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if LOCAL_NEWS_DEPS.exists():
    sys.path.insert(0, str(LOCAL_NEWS_DEPS))
if LOCAL_DEPS.exists():
    sys.path.append(str(LOCAL_DEPS))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import feedparser
except Exception:
    feedparser = None

from constants import ALL_TEAMS


DATA_DIR = PROJECT_ROOT / "data" / "processed"
FEATURES_PATH = DATA_DIR / "features.csv"
SENTIMENT_FEATURES_PATH = DATA_DIR / "sentiment_features.csv"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
SENTIMENT_COLUMNS = ["home_sentiment", "away_sentiment", "sentiment_diff"]

POSITIVE_WORDS = [
    "win",
    "victory",
    "strong",
    "confident",
    "fit",
    "ready",
    "form",
    "impressive",
    "qualify",
    "title",
    "champion",
    "star",
    "excellent",
    "outstanding",
    "dominant",
]

NEGATIVE_WORDS = [
    "injury",
    "injured",
    "doubt",
    "suspended",
    "loss",
    "defeat",
    "weak",
    "struggle",
    "crisis",
    "concern",
    "worry",
    "miss",
    "ruled out",
    "setback",
    "poor",
    "worst",
]

TEAM_ALIASES = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Czechia": "Czech Republic",
    "Curacao": "Curaçao",
    "CuraÃ§ao": "Curaçao",
    "CuraÃƒÂ§ao": "Curaçao",
    "CuraÃƒÆ’Ã‚Â§ao": "Curaçao",
}


def canonical_team(team: object) -> str:
    value = str(team)
    return TEAM_ALIASES.get(value, value)


def google_news_url(team: str) -> str:
    query = quote_plus(f"{team} football 2026")
    return f"{GOOGLE_NEWS_RSS_URL}?q={query}&hl=en&gl=US&ceid=US:en"


def fetch_with_feedparser(team: str) -> list[str]:
    if feedparser is None:
        raise RuntimeError("feedparser is not available")

    feed = feedparser.parse(google_news_url(team))
    entries = getattr(feed, "entries", [])
    if getattr(feed, "bozo", False) and not entries:
        raise RuntimeError(f"Google News RSS parse failed for {team}")

    headlines = []
    for entry in entries[:10]:
        title = entry.get("title", "") if hasattr(entry, "get") else ""
        if title:
            headlines.append(str(title))
    return headlines


def fetch_with_stdlib(team: str) -> list[str]:
    with urlopen(google_news_url(team), timeout=20) as response:
        raw_xml = response.read()

    root = ET.fromstring(raw_xml)
    headlines = []
    for item in root.findall(".//item")[:10]:
        title = item.findtext("title", default="")
        if title:
            headlines.append(title)
    return headlines


def fetch_headlines(team: str) -> list[str]:
    try:
        return fetch_with_feedparser(team)
    except Exception as exc:
        print(f"{team}: feedparser unavailable or failed ({exc}); trying stdlib RSS parser")

    try:
        return fetch_with_stdlib(team)
    except Exception as exc:
        print(f"{team}: RSS fetch failed ({exc}); using neutral defaults")
        return []


def count_keyword_matches(text: str, words: list[str]) -> int:
    lower_text = text.lower()
    total = 0
    for word in words:
        pattern = r"\b" + r"\s+".join(re.escape(part) for part in word.lower().split()) + r"\b"
        total += len(re.findall(pattern, lower_text))
    return total


def headline_score(headline: str) -> float:
    words = re.findall(r"[a-zA-Z]+", headline)
    if not words:
        return 0.0

    positive = count_keyword_matches(headline, POSITIVE_WORDS)
    negative = count_keyword_matches(headline, NEGATIVE_WORDS)
    return (positive - negative) / len(words)


def sentiment_row(team: str, headlines: list[str]) -> dict[str, Any]:
    if not headlines:
        return {
            "team": team,
            "raw_sentiment": 0.0,
            "sentiment_score": 0.5,
            "positive_headlines": 0,
            "negative_headlines": 0,
            "sentiment_momentum": 0,
            "headlines_found": 0,
        }

    scores = [headline_score(headline) for headline in headlines]
    positive_count = sum(1 for score in scores if score > 0)
    negative_count = sum(1 for score in scores if score < 0)

    return {
        "team": team,
        "raw_sentiment": mean(scores),
        "sentiment_score": 0.5,
        "positive_headlines": positive_count,
        "negative_headlines": negative_count,
        "sentiment_momentum": positive_count - negative_count,
        "headlines_found": len(headlines),
    }


def build_sentiment_features() -> pd.DataFrame:
    rows = []
    teams = list(ALL_TEAMS)

    for index, team in enumerate(teams):
        print(f"Fetching sentiment headlines for {team}...")
        headlines = fetch_headlines(team)
        rows.append(sentiment_row(canonical_team(team), headlines[:10]))
        if index < len(teams) - 1:
            time.sleep(0.3)

    sentiment = pd.DataFrame(rows)
    valid_mask = sentiment["headlines_found"] > 0
    valid_raw = sentiment.loc[valid_mask, "raw_sentiment"]

    if not valid_raw.empty:
        min_raw = valid_raw.min()
        max_raw = valid_raw.max()
        if max_raw != min_raw:
            sentiment.loc[valid_mask, "sentiment_score"] = (
                (valid_raw - min_raw) / (max_raw - min_raw)
            )
        else:
            sentiment.loc[valid_mask, "sentiment_score"] = 0.5

    sentiment["raw_sentiment"] = sentiment["raw_sentiment"].round(6)
    sentiment["sentiment_score"] = sentiment["sentiment_score"].round(6)
    return sentiment[
        [
            "team",
            "raw_sentiment",
            "sentiment_score",
            "positive_headlines",
            "negative_headlines",
            "sentiment_momentum",
            "headlines_found",
        ]
    ].copy()


def merge_sentiment_into_features(features: pd.DataFrame, sentiment: pd.DataFrame) -> pd.DataFrame:
    sentiment_lookup = sentiment[["team", "sentiment_score"]].copy()
    sentiment_lookup["team_key"] = sentiment_lookup["team"].map(canonical_team)

    base = features.drop(columns=[column for column in SENTIMENT_COLUMNS if column in features.columns]).copy()
    base["home_team_key"] = base["home_team"].map(canonical_team)
    base["away_team_key"] = base["away_team"].map(canonical_team)

    home_sentiment = sentiment_lookup[["team_key", "sentiment_score"]].rename(
        columns={"team_key": "home_team_key", "sentiment_score": "home_sentiment"}
    )
    away_sentiment = sentiment_lookup[["team_key", "sentiment_score"]].rename(
        columns={"team_key": "away_team_key", "sentiment_score": "away_sentiment"}
    )

    merged = base.merge(home_sentiment, on="home_team_key", how="left")
    merged = merged.merge(away_sentiment, on="away_team_key", how="left")
    merged["home_sentiment"] = merged["home_sentiment"].fillna(0.5)
    merged["away_sentiment"] = merged["away_sentiment"].fillna(0.5)
    merged["sentiment_diff"] = merged["home_sentiment"] - merged["away_sentiment"]
    return merged.drop(columns=["home_team_key", "away_team_key"])


def print_leaderboard(sentiment: pd.DataFrame) -> None:
    ranked = sentiment.sort_values("sentiment_score", ascending=False)

    print("\nMost positive pre-tournament sentiment:")
    for row in ranked.head(10).itertuples(index=False):
        print(f"{row.team:<24} {row.sentiment_score:>6.3f}")

    print("\nMost negative pre-tournament sentiment:")
    bottom = ranked.tail(10).sort_values("sentiment_score", ascending=True)
    for row in bottom.itertuples(index=False):
        print(f"{row.team:<24} {row.sentiment_score:>6.3f}")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing feature table: {FEATURES_PATH}")

    sentiment = build_sentiment_features()
    sentiment.to_csv(SENTIMENT_FEATURES_PATH, index=False)
    print(f"\nSaved sentiment features: {SENTIMENT_FEATURES_PATH}")

    features = pd.read_csv(FEATURES_PATH)
    before_columns = len([column for column in features.columns if column not in SENTIMENT_COLUMNS])
    updated = merge_sentiment_into_features(features, sentiment)
    after_columns = len(updated.columns)
    updated.to_csv(FEATURES_PATH, index=False)

    print_leaderboard(sentiment)
    print(f"\nfeatures.csv: {before_columns} → {after_columns} columns (+3 sentiment)")


if __name__ == "__main__":
    main()
