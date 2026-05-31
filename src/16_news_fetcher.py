from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode
from urllib.request import urlopen
from typing import Any


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

import pandas as pd

try:
    import feedparser
except Exception:
    feedparser = None

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(path: Path) -> None:
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from constants import ALL_TEAMS
except ImportError:
    ALL_TEAMS = []


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


INJURIES_DIR = PROJECT_ROOT / "data" / "injuries"
PLAYER_STATUS_PATH = INJURIES_DIR / "player_status.csv"
CHANGE_LOG_PATH = INJURIES_DIR / "change_log.csv"
NEWSAPI_URL = "https://newsapi.org/v2/everything"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"

SYSTEM_PROMPT = """You are a football injury analyst. Based on news headlines
classify the player's current status. Return ONLY valid JSON
with these exact fields:
{
  'player': string,
  'team': string,
  'status': 'fit' | 'injured' | 'returning' | 'doubt' | 'unknown',
  'confidence': 'high' | 'medium' | 'low',
  'summary': string (one sentence max)
}"""

DEFAULT_STATUS = {
    "status": "unknown",
    "confidence": "low",
    "summary": "No reliable current status could be confirmed from available headlines.",
}

PLAYER_WATCHLIST = {
    "France": ["Mbappe", "Griezmann", "Tchouameni", "Camavinga", "Kante"],
    "Brazil": ["Vinicius", "Rodrygo", "Endrick", "Marquinhos", "Casemiro"],
    "Canada": ["Davies", "David", "Larin", "Buchanan", "Johnston"],
    "England": ["Bellingham", "Saka", "Foden", "Kane", "Alexander-Arnold"],
    "Germany": ["Musiala", "Wirtz", "Havertz", "Kimmich", "Rudiger"],
    "Spain": ["Yamal", "Pedri", "Rodri", "Olmo", "Morata"],
    "Portugal": ["Ronaldo", "Leao", "Fernandes", "Vitinha", "Cancelo"],
    "Argentina": ["Messi", "Di Maria", "De Paul", "Alvarez", "Mac Allister"],
    "Netherlands": ["Van Dijk", "Gakpo", "Dumfries", "Reijnders", "Depay"],
    "Belgium": ["De Bruyne", "Lukaku", "Tielemans", "Doku"],
    "Croatia": ["Modric", "Kovacic", "Gvardiol", "Perisic"],
    "Morocco": ["Hakimi", "Amrabat", "En-Nesyri", "Bounou"],
    "United States": ["Pulisic", "McKennie", "Adams", "Weah", "Turner"],
    "Mexico": ["Ochoa", "Lozano", "Alvarez H", "Antuna"],
    "Japan": ["Mitoma", "Kubo", "Endo", "Minamino"],
    "Senegal": ["Mane", "Sarr", "Diatta", "Kouyate"],
    "Colombia": ["James Rodriguez", "Arias", "Cuadrado", "Cuesta"],
    "Uruguay": ["Valverde", "Nunez", "Bentancur"],
    "Norway": ["Haaland", "Odegaard", "Sorloth"],
    "South Korea": ["Son", "Lee Kang-in", "Hwang Hee-chan"],
    "Australia": ["Leckie", "Irvine", "Ryan"],
    "Ecuador": ["Caicedo", "Valencia E", "Plata"],
    "Ghana": ["Kudus", "Partey", "Salisu"],
    "Switzerland": ["Xhaka", "Shaqiri", "Akanji"],
    "Austria": ["Alaba", "Sabitzer", "Arnautovic"],
    "Sweden": ["Isak", "Kulusevski", "Forsberg"],
    "Tunisia": ["Msakni", "Slimane", "Talbi"],
    "Egypt": ["Salah", "El-Shenawy", "Trezeguet"],
    "Iran": ["Azmoun", "Taremi", "Jahanbakhsh"],
    "Saudi Arabia": ["Al-Dawsari", "Balghunaim", "Al-Shahrani"],
    "Scotland": ["Robertson", "McTominay", "McGinn"],
    "Turkey": ["Calhanoglu", "Guler", "Yildiz"],
    "Czechia": ["Soucek", "Schick", "Hlozek"],
    "Algeria": ["Mahrez", "Bennacer", "Slimani"],
    "Ivory Coast": ["Haller", "Sangare", "Fofana"],
    "Paraguay": ["Almiron", "Sanabria", "Enciso"],
    "DR Congo": ["Bakambu", "Kayembe", "Mbokani"],
    "Bosnia-Herzegovina": ["Dzeko", "Pjanic", "Kolasinac"],
    "Panama": ["Davis", "Fajardo", "Murillo"],
    "Qatar": ["Al-Moez", "Muntari", "Boudiaf"],
    "Cape Verde": ["Andrade", "Lopes", "Varela"],
    "Iraq": ["Mohanad Ali", "Aymen Hussein"],
    "Jordan": ["Al-Rawabdeh", "Abou Saleh"],
    "Uzbekistan": ["Shomurodov", "Tursunov"],
    "Haiti": ["Altidor", "Herard"],
    "Curacao": ["Dos Santos", "Bacuna"],
    "South Africa": ["Tau", "Zwane", "Dolly"],
    "New Zealand": ["Wood", "McGlinchey"],
}

WATCHLIST_TEAM_ALIASES = {
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "Czech Republic": "Czechia",
    "Curaçao": "Curacao",
    "CuraÃ§ao": "Curacao",
}

SAMPLE_HEADLINES = {
    "Mbappe": [
        "Mbappe returns to France training and is available after minor fitness concern",
    ],
    "Bellingham": [
        "Bellingham faces late fitness test as England wait on midfield update",
    ],
    "Musiala": [
        "Musiala ruled out of Germany session with injury concern before tournament warm-up",
    ],
    "Vinicius": [
        "Vinicius completes comeback from hamstring issue and rejoins Brazil squad",
    ],
    "Haaland": [
        "Haaland declared fit as Norway receive major availability boost",
    ],
    "Salah": [
        "Salah remains a doubt for Egypt after missing training with fitness issue",
    ],
    "Rodri": [
        "Rodri available again as Spain receive fitness boost before summer fixtures",
        "Spain staff confident Rodri is fit after carefully managed return",
    ],
    "Pedri": [
        "Pedri remains a doubt as Spain monitor fitness after latest Barcelona setback",
        "Spain wait on Pedri availability before naming final midfield plans",
    ],
    "Aymen Hussein": [
        "Aymen Hussein ruled fit after Iraq striker returns to full training",
        "Iraq receive comeback boost as Aymen Hussein available for selection",
    ],
    "Mohanad Ali": [
        "Mohanad Ali suspended for Iraq qualifier after disciplinary ruling",
    ],
    "Altidor": [
        "Altidor expected to be available for Haiti after shaking off knock",
    ],
    "Herard": [],
}


def newsapi_key() -> str:
    return os.getenv("NEWSAPI_KEY", "").strip()


def use_sample_news() -> bool:
    return os.getenv("USE_SAMPLE_NEWS", "").strip() == "1"


def fetch_google_news_for_player(player: str, team: str, page_size: int = 5) -> list[dict[str, str]]:
    if feedparser is None:
        raise RuntimeError("feedparser is not available")

    query = quote_plus(f"{player} football injury fitness")
    url = f"{GOOGLE_NEWS_RSS_URL}?q={query}&hl=en&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    if getattr(feed, "bozo", False) and not getattr(feed, "entries", []):
        raise RuntimeError(f"Google News RSS parse failed for {player}")

    rows = []
    for entry in feed.entries[:page_size]:
        headline = entry.get("title", "")
        if not headline:
            continue
        rows.append(
            {
                "player": player,
                "team": team,
                "headline": headline,
                "published": entry.get("published", ""),
                "source": "Google News RSS",
            }
        )
    return rows


def fetch_newsapi_for_player(player: str, team: str, days_back: int = 3) -> list[dict[str, str]]:
    api_key = newsapi_key()
    if not api_key:
        return []

    from_date = (date.today() - timedelta(days=days_back)).isoformat()
    query = (
        f'"{player}" injury OR fitness OR suspended OR doubt '
        "OR return OR comeback OR available OR ruled out"
    )
    params = {
        "q": query,
        "from": from_date,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": api_key,
    }

    try:
        url = f"{NEWSAPI_URL}?{urlencode(params)}"
        with urlopen(url, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"NewsAPI error for {team} / {player}: {exc}")
        payload = {"articles": []}

    rows = []
    for article in payload.get("articles", []):
        headline = article.get("title") or ""
        if not headline:
            continue
        rows.append(
            {
                "player": player,
                "team": team,
                "headline": headline,
                "published": article.get("publishedAt") or "",
                "source": (article.get("source") or {}).get("name") or "",
            }
        )
    return rows


def fetch_team_news(team: str, players: list[str], days_back: int = 3) -> list[dict[str, str]]:
    rows = []

    for player in players:
        try:
            rows.extend(fetch_google_news_for_player(player, team))
        except Exception as exc:
            print(f"Google News RSS error for {team} / {player}: {exc}")
            rows.extend(fetch_newsapi_for_player(player, team, days_back=days_back))

        time.sleep(0.2)

    return rows


def sample_news_for_player(player: str, team: str) -> list[dict[str, str]]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "player": player,
            "team": team,
            "headline": headline,
            "published": now,
            "source": "Sample data",
        }
        for headline in SAMPLE_HEADLINES.get(player, [])
    ]


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def unknown_status(player: str, team: str, summary: str | None = None) -> dict[str, str]:
    return {
        "player": player,
        "team": team,
        "status": DEFAULT_STATUS["status"],
        "confidence": DEFAULT_STATUS["confidence"],
        "summary": summary or DEFAULT_STATUS["summary"],
    }


def classify_player_status(
    player: str,
    team: str,
    headlines: list[dict[str, str]] | list[str],
) -> dict[str, str]:
    if not headlines:
        return unknown_status(player, team)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return unknown_status(player, team, "OpenAI API key was not available for classification.")
    if OpenAI is None:
        return unknown_status(player, team, "OpenAI package was not available for classification.")

    headline_lines = []
    for item in headlines:
        if isinstance(item, dict):
            headline_lines.append(f"- {item.get('headline', '')}")
        else:
            headline_lines.append(f"- {item}")

    user_message = f"Player: {player}\nTeam: {team}\n\nHeadlines:\n" + "\n".join(headline_lines)

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            max_tokens=250,
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        parsed = extract_json(content)
    except Exception as exc:
        print(f"Classification error for {team} / {player}: {exc}")
        return unknown_status(player, team, "Status classification failed.")

    status = str(parsed.get("status", "unknown")).lower()
    confidence = str(parsed.get("confidence", "low")).lower()
    if status not in {"fit", "injured", "returning", "doubt", "unknown"}:
        status = "unknown"
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    return {
        "player": str(parsed.get("player") or player),
        "team": str(parsed.get("team") or team),
        "status": status,
        "confidence": confidence,
        "summary": str(parsed.get("summary") or DEFAULT_STATUS["summary"]),
    }


def run_news_scan(teams: list[str] | tuple[str, ...] = ALL_TEAMS) -> list[dict[str, str]]:
    use_sample_data = use_sample_news()
    statuses = []

    for team in teams:
        watchlist_team = WATCHLIST_TEAM_ALIASES.get(team, team)
        players = PLAYER_WATCHLIST.get(watchlist_team, [])
        if not players:
            continue

        team_news = [] if use_sample_data else fetch_team_news(watchlist_team, players)
        by_player: dict[str, list[dict[str, str]]] = {player: [] for player in players}
        for article in team_news:
            by_player.setdefault(article["player"], []).append(article)

        for player in players:
            headlines = (
                sample_news_for_player(player, watchlist_team)
                if use_sample_data
                else by_player.get(player, [])
            )
            status = classify_player_status(player, watchlist_team, headlines)
            statuses.append(status)

    return statuses


def load_previous_statuses() -> pd.DataFrame:
    if not PLAYER_STATUS_PATH.exists():
        return pd.DataFrame(columns=["player", "team", "status", "confidence", "summary", "updated_at"])
    return pd.read_csv(PLAYER_STATUS_PATH)


def detect_changes(new_statuses: pd.DataFrame, previous_statuses: pd.DataFrame) -> list[dict[str, str]]:
    if previous_statuses.empty:
        return []

    previous_lookup = {
        (row.player, row.team): row.status
        for row in previous_statuses.itertuples(index=False)
        if hasattr(row, "player") and hasattr(row, "team") and hasattr(row, "status")
    }
    changes = []

    for row in new_statuses.itertuples(index=False):
        old_status = previous_lookup.get((row.player, row.team))
        if old_status is None:
            continue
        if old_status != row.status and row.confidence in {"medium", "high"}:
            changes.append(
                {
                    "player": row.player,
                    "team": row.team,
                    "old_status": old_status,
                    "new_status": row.status,
                    "confidence": row.confidence,
                    "summary": row.summary,
                }
            )

    return changes


def append_change_log(changes: list[dict[str, str]], timestamp: str) -> None:
    if not changes:
        if not CHANGE_LOG_PATH.exists():
            pd.DataFrame(
                columns=[
                    "timestamp",
                    "player",
                    "team",
                    "old_status",
                    "new_status",
                    "confidence",
                    "summary",
                ]
            ).to_csv(CHANGE_LOG_PATH, index=False)
        return

    rows = [{"timestamp": timestamp, **change} for change in changes]
    changes_frame = pd.DataFrame(
        rows,
        columns=[
            "timestamp",
            "player",
            "team",
            "old_status",
            "new_status",
            "confidence",
            "summary",
        ],
    )

    if CHANGE_LOG_PATH.exists():
        existing = pd.read_csv(CHANGE_LOG_PATH)
        changes_frame = pd.concat([existing, changes_frame], ignore_index=True)

    changes_frame.to_csv(CHANGE_LOG_PATH, index=False)


def save_statuses(statuses: list[dict[str, str]], timestamp: str) -> pd.DataFrame:
    rows = [{**status, "updated_at": timestamp} for status in statuses]
    frame = pd.DataFrame(
        rows,
        columns=["player", "team", "status", "confidence", "summary", "updated_at"],
    )
    frame.to_csv(PLAYER_STATUS_PATH, index=False)
    return frame


def print_summary(statuses: pd.DataFrame, changes: list[dict[str, str]]) -> None:
    print("\nNews scan summary")
    print("-" * 72)
    print(f"Total players scanned: {len(statuses)}")

    print("\nStatus breakdown")
    breakdown = statuses["status"].value_counts().reindex(
        ["fit", "injured", "returning", "doubt", "unknown"],
        fill_value=0,
    )
    for status, count in breakdown.items():
        print(f"{status}: {count}")

    print("\nStatus changes")
    if not changes:
        print("None")
        return

    for change in changes:
        print(
            f"{change['player']} ({change['team']}): "
            f"{change['old_status']} -> {change['new_status']} "
            f"[{change['confidence']}] {change['summary']}"
        )


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    INJURIES_DIR.mkdir(parents=True, exist_ok=True)

    if use_sample_news():
        print("USE_SAMPLE_NEWS=1 set. Using sample headline data for testing.")

    previous_statuses = load_previous_statuses()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    statuses = run_news_scan()
    statuses_frame = save_statuses(statuses, timestamp)
    changes = detect_changes(statuses_frame, previous_statuses)
    append_change_log(changes, timestamp)
    print_summary(statuses_frame, changes)


if __name__ == "__main__":
    main()
