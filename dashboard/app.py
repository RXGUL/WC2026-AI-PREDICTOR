from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
import streamlit as st

st.set_page_config(
    page_title="WC2026 AI Predictor",
    page_icon="\u26bd",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Archivo+Black&display=swap');

    /* Global */
    html, body, [class*="css"] {
        font-family: 'Space Mono', monospace !important;
        background-color: #0a0a0a !important;
        color: #f0f0f0 !important;
    }

    /* Retro diagonal grid background */
    .stApp {
        background-color: #0a0a0a !important;
        background-image:
            linear-gradient(rgba(198,11,30,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(198,11,30,0.025) 1px, transparent 1px) !important;
        background-size: 48px 48px !important;
    }

    /* Main title */
    h1 {
        font-family: 'Bebas Neue', cursive !important;
        font-size: 52px !important;
        letter-spacing: 6px !important;
        color: #ffffff !important;
        border-bottom: 3px solid #C60B1E !important;
        padding-bottom: 8px !important;
        margin-bottom: 4px !important;
    }

    /* All other headings */
    h2, h3 {
        font-family: 'Archivo Black', sans-serif !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        color: #cccccc !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: #0d0d0d !important;
        border-bottom: 2px solid #1a1a1a !important;
        gap: 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Archivo Black', sans-serif !important;
        font-size: 11px !important;
        font-weight: 400 !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        color: #888 !important;
        padding: 12px 24px !important;
        border-radius: 0 !important;
        border-right: 1px solid #1a1a1a !important;
    }

    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        font-weight: 700 !important;
        background: rgba(198,11,30,0.1) !important;
        border-top: 3px solid #C60B1E !important;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #0d1117 !important;
        border: 1px solid #222 !important;
        border-top: 2px solid #C60B1E !important;
        border-radius: 6px !important;
        padding: 16px !important;
    }

    [data-testid="metric-container"] label {
        font-family: 'Space Mono', monospace !important;
        font-size: 9px !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        color: #999 !important;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-family: 'Bebas Neue', cursive !important;
        font-size: 36px !important;
        letter-spacing: 2px !important;
        color: #ffffff !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #050505 !important;
        border-right: 1px solid #1a1a1a !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-family: 'Bebas Neue', cursive !important;
        color: #C60B1E !important;
        letter-spacing: 4px !important;
    }

    /* Buttons */
    .stButton > button {
        font-family: 'Archivo Black', sans-serif !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        background: #C60B1E !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 10px 24px !important;
    }

    .stButton > button:hover {
        background: #a00818 !important;
        transform: translateY(-1px) !important;
    }

    /* Selectbox */
    .stSelectbox [data-baseweb="select"] {
        background: #111 !important;
        border: 1px solid #2a2a2a !important;
        font-family: 'Space Mono', monospace !important;
    }

    /* Dataframes */
    .stDataFrame {
        border: 1px solid #1e1e1e !important;
    }

    /* Kill all Streamlit default colored containers */
    [data-testid="stAlert"] {
        display: none !important;
    }

    div[style*="background-color: rgb(255, 243, 205)"],
    div[style*="background-color: rgb(255, 228, 225)"],
    div[style*="background-color: rgb(240, 242, 246)"],
    div[style*="background: rgb(255"] {
        background-color: transparent !important;
        border: none !important;
    }

    /* Dataframe highlight removal */
    [data-testid="stDataFrame"] td[style*="background"] {
        background-color: #0d1117 !important;
    }

    /* Remove any selected row highlight in tables */
    .stDataFrame tbody tr:hover {
        background-color: #161b22 !important;
    }

    /* Info/warning boxes */
    .stInfo {
        background: #0d1a1a !important;
        border-left: 3px solid #00B4D8 !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 12px !important;
        line-height: 1.8 !important;
    }

    /* Divider */
    hr {
        border-color: #1a1a1a !important;
    }

    /* Footer */
    .footer-text {
        font-family: 'Space Mono', monospace !important;
        font-size: 9px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        color: #999 !important;
        text-align: center !important;
        padding: 16px 0 !important;
        border-top: 1px solid #1a1a1a !important;
    }

    /* Plotly chart backgrounds */
    .js-plotly-plot .plotly {
        background: transparent !important;
    }

    /* Tab 2 accent (cyan) */
    .tab2-header {
        color: #00B4D8 !important;
        border-bottom-color: #00B4D8 !important;
    }

    /* Tab 3 accent (orange) */
    .tab3-header {
        color: #FF6B35 !important;
    }

    /* Tab 4 accent (neon green) */
    .tab4-header {
        color: #39FF14 !important;
    }

    /* Decorative watermark trophies */
    .trophy-watermark {
        position: fixed;
        font-size: 120px;
        opacity: 0.03;
        pointer-events: none;
        z-index: 0;
        filter: grayscale(1);
    }

    /* Tab transition celebration overlay */
    .celebration-banner {
        position: fixed;
        bottom: 32px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg,
            rgba(198,11,30,0.95), rgba(0,0,0,0.9));
        color: white;
        padding: 12px 32px;
        border-radius: 4px;
        font-family: 'Bebas Neue', cursive;
        font-size: 22px;
        letter-spacing: 6px;
        border-left: 4px solid #FFD700;
        border-right: 4px solid #FFD700;
        z-index: 9999;
        animation: celebFade 1.2s ease forwards;
        pointer-events: none;
        white-space: nowrap;
    }

    @keyframes celebFade {
        0%   { opacity: 0; transform: translateX(-50%) translateY(10px); }
        15%  { opacity: 1; transform: translateX(-50%) translateY(0px); }
        70%  { opacity: 1; transform: translateX(-50%) translateY(0px); }
        100% { opacity: 0; transform: translateX(-50%) translateY(-8px); }
    }

    /* Tab hover effect */
    .stTabs [data-baseweb="tab"]:hover {
        color: #888 !important;
        background: rgba(255,255,255,0.03) !important;
        transition: all 0.2s ease !important;
    }

    /* Smooth content transitions */
    .stTabs [data-baseweb="tab-panel"] {
        animation: tabFadeIn 0.4s ease forwards;
    }

    @keyframes tabFadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Trophy watermark - CSS only, no image needed */
    .stApp::after {
        content: "⚽";
        position: fixed;
        right: -60px;
        top: 50%;
        transform: translateY(-50%) rotate(-15deg);
        font-size: 420px;
        opacity: 0.018;
        pointer-events: none;
        z-index: 0;
        line-height: 1;
        filter: grayscale(1);
    }

    .stApp::before {
        content: "🏆";
        position: fixed;
        right: 40px;
        bottom: 60px;
        font-size: 180px;
        opacity: 0.025;
        pointer-events: none;
        z-index: 0;
        transform: rotate(8deg);
        filter: grayscale(1);
    }
    @media (max-width: 768px) {

        /* 1. Shrink the massive title on mobile */
        h1, .main-title {
            font-size: 1.6rem !important;
            line-height: 1.2 !important;
        }

        /* 2. Tabs — make them horizontally scrollable so all tabs are reachable */
        [data-testid="stTabs"] > div:first-child {
            overflow-x: auto !important;
            white-space: nowrap !important;
            -webkit-overflow-scrolling: touch !important;
            scrollbar-width: none !important;
            display: flex !important;
            flex-wrap: nowrap !important;
        }
        [data-testid="stTabs"] > div:first-child::-webkit-scrollbar {
            display: none !important;
        }
        [data-testid="stTabs"] button {
            font-size: 10px !important;
            padding: 8px 12px !important;
            white-space: nowrap !important;
            flex-shrink: 0 !important;
        }

        /* 3. Fix dataframe/table white background on mobile */
        [data-testid="stDataFrame"] {
            background-color: #0d1117 !important;
        }
        [data-testid="stDataFrame"] * {
            background-color: #0d1117 !important;
            color: #cccccc !important;
        }
        iframe[title="st_aggrid"] {
            background-color: #0d1117 !important;
        }

        /* 4. Hide Plotly toolbar on mobile — too cluttered */
        .modebar {
            display: none !important;
        }

        /* 5. Plotly charts — contain within screen, no horizontal overflow */
        [data-testid="stPlotlyChart"] > div {
            max-width: 100% !important;
            overflow-x: hidden !important;
        }

        /* 6. Subtitle line — wrap instead of overflow */
        .subtitle-bar, [data-testid="stMarkdownContainer"] p {
            white-space: normal !important;
            font-size: 9px !important;
            letter-spacing: 0.5px !important;
            line-height: 1.8 !important;
        }

        /* 7. Sidebar collapsed indicator — keep it minimal */
        [data-testid="collapsedControl"] {
            top: 10px !important;
        }
    }
    </style>
    <script>
    const MESSAGES = [
        "SIUUU!", "VAMOS!", "JOGA BONITO", "GOAL!",
        "FORZA!", "OLE OLE OLE", "WHAT A STRIKE!",
        "THE BEAUTIFUL GAME", "INTO THE FINAL THIRD...",
        "CHAMPIONS ARE MADE HERE", "MAGIC IN MOTION",
        "FOOTBALL HERITAGE", "QUE GOLAZO!"
    ];

    let lastTab = null;

    function showCelebration() {
        const existing = document.querySelector('.celebration-banner');
        if (existing) existing.remove();

        const msg = MESSAGES[Math.floor(Math.random() * MESSAGES.length)];
        const banner = document.createElement('div');
        banner.className = 'celebration-banner';
        banner.textContent = msg;
        document.body.appendChild(banner);

        setTimeout(() => {
            if (banner.parentNode) banner.remove();
        }, 1400);
    }

    function watchTabs() {
        const tabs = document.querySelectorAll(
            '[data-baseweb="tab"]'
        );
        tabs.forEach((tab, i) => {
            tab.addEventListener('click', () => {
                if (lastTab !== i) {
                    lastTab = i;
                    setTimeout(showCelebration, 100);
                }
            });
        });
    }

    const observer = new MutationObserver(() => {
        watchTabs();
    });
    observer.observe(document.body, {
        childList: true, subtree: true
    });

    setTimeout(watchTabs, 1000);
    </script>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="trophy-watermark"
         style="top:10%;right:2%;transform:rotate(15deg)">
         &#127942;
    </div>
    <div class="trophy-watermark"
         style="bottom:15%;left:1%;transform:rotate(-20deg);font-size:80px">
         &#9917;
    </div>
    <div class="trophy-watermark"
         style="top:50%;right:1%;transform:rotate(-10deg);font-size:60px">
         &#127941;
    </div>
    """,
    unsafe_allow_html=True,
)

from datetime import datetime
import html
import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

try:
    from constants import ALL_TEAMS, HOST_NATIONS, WC2026_GROUPS
except ImportError as e:
    import streamlit as st
    st.error(f"Cannot import constants: {e}")
    st.stop()

load_dotenv()


DATA_DIR = PROJECT_ROOT / "data" / "processed"
INJURIES_DIR = PROJECT_ROOT / "data" / "injuries"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
MODELS_DIR = PROJECT_ROOT / "models"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GITHUB_URL = "https://github.com/RXGUL/wc2026-ai-predictor"
FOOTER_TEXT = (
    "WC2026 AI Predictor · Built by Ragul Velmurugan · "
    "XGBoost + Monte Carlo + GPT-4o + LangGraph · "
    "GitHub: github.com/RXGUL/WC2026-AI-PREDICTOR"
)


def load_module_from_path(module_name: str, path: Path):
    from importlib import util

    if not path.exists():
        return None
    spec = util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TEAM_ALIASES = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Czechia": "Czech Republic",
    "Curacao": "Curaçao",
    "CuraÃ§ao": "Curaçao",
}


def display_team(team: str) -> str:
    return TEAM_ALIASES.get(str(team), str(team))


TEAM_LOOKUP_ALIASES = {
    "Bosnia and Herzegovina": ["Bosnia and Herzegovina", "Bosnia-Herzegovina"],
    "Bosnia-Herzegovina": ["Bosnia-Herzegovina", "Bosnia and Herzegovina"],
    "Czech Republic": ["Czech Republic", "Czechia"],
    "Czechia": ["Czechia", "Czech Republic"],
    "CuraÃ§ao": ["CuraÃ§ao", "CuraÃƒÂ§ao", "Curacao", "Curaçao"],
    "CuraÃƒÂ§ao": ["CuraÃƒÂ§ao", "CuraÃ§ao", "Curacao", "Curaçao"],
    "Curaçao": ["Curaçao", "CuraÃ§ao", "CuraÃƒÂ§ao", "Curacao"],
    "Curacao": ["Curacao", "CuraÃ§ao", "CuraÃƒÂ§ao", "Curaçao"],
}


def team_candidates(team: str) -> list[str]:
    candidates = TEAM_LOOKUP_ALIASES.get(str(team), [str(team)])
    return list(dict.fromkeys(candidates + [display_team(team)]))


def team_rows(frame: pd.DataFrame, team: str, column: str = "team") -> pd.DataFrame:
    if frame.empty or column not in frame.columns:
        return frame.iloc[0:0].copy()
    return frame[frame[column].astype(str).isin(team_candidates(team))].copy()


def first_team_row(frame: pd.DataFrame, team: str, column: str = "team") -> pd.Series:
    rows = team_rows(frame, team, column)
    if rows.empty:
        return pd.Series(dtype=object)
    return rows.iloc[0]


def report_for_team(reports: dict[str, str], team: str) -> str | None:
    for candidate in team_candidates(team):
        if candidate in reports:
            return reports[candidate]
    return None


def group_lookup() -> dict[str, str]:
    lookup = {}
    for group_name, teams in WC2026_GROUPS.items():
        for team in teams:
            lookup[display_team(team)] = group_name
            lookup[str(team)] = group_name
    return lookup


@st.cache_data
def load_csv(path: str, columns: tuple[str, ...] = ()) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        try:
            label = csv_path.relative_to(PROJECT_ROOT)
        except ValueError:
            label = csv_path
        st.warning(f"Missing data file: {label}")
        return pd.DataFrame(columns=list(columns))
    return pd.read_csv(csv_path)


@st.cache_data
def load_reports(path: str) -> dict[str, str]:
    report_path = Path(path)
    if not report_path.exists():
        st.warning("Missing report file: outputs/reports/all_reports.json")
        return {}
    return json.loads(report_path.read_text(encoding="utf-8"))


@st.cache_data(ttl=60)
def load_matches():
    import requests
    from dotenv import load_dotenv

    load_dotenv()
    key = os.getenv("FOOTBALL_API_KEY", "")
    if not key:
        return None
    try:
        headers = {"X-Auth-Token": key}
        r = requests.get(
            "https://api.football-data.org/v4/competitions/WC/matches",
            headers=headers,
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("matches", [])
        return None
    except Exception:
        return None


@st.cache_data
def load_reference_files() -> dict[str, object]:
    master_df = load_csv(
        str(DATA_DIR / "master_teams.csv"),
        (
            "team",
            "group",
            "confederation",
            "is_host",
            "fifa_rank",
            "squad_value_m",
            "avg_ca",
            "composure",
            "avg_mentality",
            "injured_count",
            "availability_score",
        ),
    )
    try:
        squad_df = pd.read_csv(DATA_DIR / "squad_values.csv")
        master_df = master_df.merge(
            squad_df[["team", "squad_value_m"]],
            on="team",
            how="left",
            suffixes=("_drop", ""),
        )
        if "squad_value_m_drop" in master_df.columns:
            master_df = master_df.drop(columns=["squad_value_m_drop"])
    except Exception:
        pass

    return {
        "master": master_df,
        "elo": load_csv(str(DATA_DIR / "elo_ratings.csv"), ("team", "elo", "matches_played")),
        "upsets": load_csv(
            str(DATA_DIR / "upset_predictions.csv"),
            ("group", "favourite", "underdog", "upset_prob", "elo_gap"),
        ),
        "features": load_csv(str(DATA_DIR / "feature_importance.csv"), ("rank", "feature", "importance")),
        "team_shap": pd.read_csv(DATA_DIR / "team_shap_summary.csv")
        if (DATA_DIR / "team_shap_summary.csv").exists()
        else pd.DataFrame(
            columns=["team", "top_feature_1", "shap_1", "top_feature_2", "shap_2", "top_feature_3", "shap_3"]
        ),
        "pressure": load_csv(
            str(DATA_DIR / "pressure_index.csv"),
            ("team", "pressure_index", "knockout_win_rate"),
        ),
        "player_status": load_csv(
            str(INJURIES_DIR / "player_status.csv"),
            ("player", "team", "status", "confidence", "summary", "updated_at"),
        ),
        "change_log": load_csv(
            str(INJURIES_DIR / "change_log.csv"),
            ("timestamp", "player", "team", "old_status", "new_status", "confidence", "summary"),
        ),
        "reports": load_reports(str(REPORTS_DIR / "all_reports.json")),
    }


@st.cache_data(ttl=300)
def load_from_supabase():
    import requests
    from dotenv import load_dotenv

    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL or SUPABASE_KEY. Refusing to fall back to local trophy CSV."
        )

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    try:
        # Trophy predictions
        r1 = requests.get(
            f"{url}/rest/v1/trophy_predictions"
            "?select=*&order=trophy_probability.desc",
            headers=headers,
            timeout=10,
        )
        r1.raise_for_status()
        trophy_df = pd.DataFrame(r1.json())
        if trophy_df.empty or "trophy_probability" not in trophy_df.columns:
            raise RuntimeError("Supabase returned no trophy prediction rows.")

        # Analyst reports
        r2 = requests.get(
            f"{url}/rest/v1/analyst_reports"
            "?select=team,report_text",
            headers=headers,
            timeout=10,
        )
        r2.raise_for_status()
        reports = {r["team"]: r["report_text"] for r in r2.json()}

        # Player status
        r3 = requests.get(
            f"{url}/rest/v1/player_status?select=*",
            headers=headers,
            timeout=10,
        )
        r3.raise_for_status()
        status_df = pd.DataFrame(r3.json())

        # Change log
        r4 = requests.get(
            f"{url}/rest/v1/change_log"
            "?select=*&order=logged_at.desc&limit=100",
            headers=headers,
            timeout=10,
        )
        r4.raise_for_status()
        changes_df = pd.DataFrame(r4.json())

        return trophy_df, reports, status_df, changes_df

    except Exception as e:
        raise RuntimeError(f"Supabase REST failed: {e}") from e


@st.cache_data
def load_player_watchlist() -> tuple[dict[str, list[str]], dict[str, str]]:
    news_fetcher = load_module_from_path("dashboard_news_fetcher", PROJECT_ROOT / "src" / "16_news_fetcher.py")
    if news_fetcher is None:
        return {}, {}
    return (
        getattr(news_fetcher, "PLAYER_WATCHLIST", {}),
        getattr(news_fetcher, "WATCHLIST_TEAM_ALIASES", {}),
    )


def file_updated_at(path: Path) -> str:
    if not path.exists():
        return "Unavailable"
    updated = datetime.fromtimestamp(path.stat().st_mtime)
    return updated.strftime("%b %d, %Y %I:%M %p")


def prepare_trophy_table(trophy: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    group_map = group_lookup()
    trophy_table = trophy.copy()
    trophy_table["Team"] = trophy_table["team"].map(display_team)

    master_groups = master.copy()
    master_groups["Team"] = master_groups["team"].map(display_team)
    master_groups = master_groups[["Team", "group"]].drop_duplicates("Team")
    trophy_table = trophy_table.merge(master_groups, on="Team", how="left")
    trophy_table["Group"] = trophy_table["group"].fillna(trophy_table["Team"].map(group_map))
    trophy_table["Rank"] = range(1, len(trophy_table) + 1)

    return trophy_table


def rank_colour(rank: int) -> str:
    if rank <= 8:
        return "#2E7D32"
    if rank <= 16:
        return "#1565C0"
    return "#9E9E9E"


def render_sidebar() -> None:
    st.sidebar.title("WC2026 AI Predictor")
    st.sidebar.caption("Data source: Supabase live database")
    st.sidebar.link_button("GitHub repo", GITHUB_URL)
    st.sidebar.markdown(
        "AI-powered WC2026 prediction system. "
        "XGBoost + Monte Carlo + GPT-4o + LangGraph agent."
    )
    render_agent_sidebar_status()
    st.sidebar.markdown(
        """
        <div style="font-family:'Space Mono',monospace;
        font-size:10px;color:#999;margin-top:8px">
        Match data: football-data.org
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_sidebar_status() -> None:
    change_log_path = INJURIES_DIR / "change_log.csv"
    player_status_path = INJURIES_DIR / "player_status.csv"
    if not change_log_path.exists():
        st.sidebar.markdown(
            """
            <div style="font-family:'Space Mono',monospace;font-size:10px;color:#999;margin-top:16px">
            Agent: Monitoring active
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    try:
        changes = pd.read_csv(change_log_path)
        statuses = pd.read_csv(player_status_path) if player_status_path.exists() else pd.DataFrame()
    except Exception:
        changes = pd.DataFrame()
        statuses = pd.DataFrame()

    if changes.empty:
        status_html = "Agent: Monitoring active"
    else:
        latest = changes.sort_values("timestamp", ascending=False).iloc[0]
        flagged_count = 0
        if not statuses.empty and "status" in statuses.columns:
            flagged_count = int((statuses["status"].astype(str).str.lower() != "unknown").sum())
        status_html = (
            f"Last agent scan: {html.escape(str(latest.get('timestamp', 'Unavailable')))}<br>"
            f"Players flagged: {flagged_count}<br>"
            f"Most recent change: {html.escape(str(latest.get('player', 'Unknown')))} "
            f"({html.escape(str(latest.get('team', 'Unknown')))}): "
            f"{html.escape(str(latest.get('old_status', 'unknown')))} → "
            f"{html.escape(str(latest.get('new_status', 'unknown')))}"
        )

    st.sidebar.markdown(
        f"""
        <div style="font-family:'Space Mono',monospace;font-size:10px;color:#999;margin-top:16px;line-height:1.7">
        {status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_model_status() -> None:
    required_models = [MODELS_DIR / "xgboost_model.pkl", MODELS_DIR / "feature_list.json"]
    if any(not model_path.exists() for model_path in required_models):
        st.info("Model loading...")


def render_footer() -> None:
    st.divider()
    st.markdown(
        """
        <div class="footer-text">
        WC2026 AI Predictor &nbsp;·&nbsp;
        XGBoost + Monte Carlo + GPT-4o + LangGraph &nbsp;·&nbsp;
        Built by Ragul Velmurugan &nbsp;·&nbsp;
        github.com/RXGUL/WC2026-AI-PREDICTOR
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tab1_metric_card(
    label: str,
    value: str,
    detail: str,
    border_color: str,
    css_class: str = "",
) -> None:
    class_attr = f"metric-card {css_class}".strip()
    st.markdown(
        f"""
        <div class="{class_attr}" style="
            background:#0d1117;
            border:1px solid #222;
            border-top:2px solid {border_color};
            border-radius:8px;
            padding:16px;
            min-height:118px;
        ">
            <div style="
                font-family:'Space Mono',monospace;
                font-size:9px;
                letter-spacing:3px;
                text-transform:uppercase;
                color:#999;
                margin-bottom:8px;
            ">{label}</div>
            <div style="
                font-family:'Bebas Neue',cursive;
                font-size:36px;
                letter-spacing:2px;
                line-height:1;
                color:#ffffff;
                overflow-wrap:anywhere;
            ">{value}</div>
            <div style="
                font-family:'Space Mono',monospace;
                font-size:12px;
                color:#888;
                margin-top:8px;
            ">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def team_probability_from_table(trophy_table: pd.DataFrame, team: str) -> float:
    if trophy_table.empty:
        return 0.0
    rows = trophy_table[
        trophy_table["team"].astype(str).isin(team_candidates(team))
        | trophy_table["Team"].astype(str).isin(team_candidates(team))
    ]
    if rows.empty:
        return 0.0
    return float(rows.iloc[0].get("trophy_probability", 0) or 0)


def render_group_stage_bracket(trophy_table: pd.DataFrame) -> None:
    st.markdown("---")
    st.markdown("<h2>WC2026 Group Stage Bracket</h2>", unsafe_allow_html=True)

    group_items = list(WC2026_GROUPS.items())
    for group_index in range(0, len(group_items), 3):
        columns = st.columns(3)
        for column, (group, teams) in zip(columns, group_items[group_index : group_index + 3]):
            ranked_group = sorted(
                [(team, team_probability_from_table(trophy_table, team)) for team in teams],
                key=lambda item: item[1],
                reverse=True,
            )
            qualifiers = {team for team, _ in ranked_group[:2]}
            team_rows_html = []
            for team, probability in ranked_group:
                color = "#2d8a2d" if team in qualifiers else "#999"
                host_badge = (
                    "<span style='color:#C60B1E;font-size:9px;margin-left:6px'>(H)</span>"
                    if team in HOST_NATIONS
                    else ""
                )
                team_rows_html.append(
                    f"""
                    <div style="display:flex;justify-content:space-between;gap:12px;
                                color:{color};font-family:'Space Mono',monospace;
                                font-size:12px;margin:5px 0">
                        <span>{html.escape(display_team(team))}{host_badge}</span>
                        <span>{probability:.2f}%</span>
                    </div>
                    """
                )
            teams_html = "".join(team_rows_html)
            with column:
                st.markdown(
                    f"""
                    <div style="background:#111;border:1px solid #222;
                    border-left:3px solid #C60B1E;border-radius:6px;
                    padding:12px;margin-bottom:8px">
                    <div style="font-family:'Archivo Black',sans-serif;
                    font-size:10px;letter-spacing:3px;color:#999;
                    margin-bottom:8px">GROUP {group}</div>
                    {teams_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def team_shap_row(team_shap: pd.DataFrame, team: str) -> pd.Series:
    if team_shap.empty or "team" not in team_shap.columns:
        return pd.Series(dtype=object)
    rows = team_shap[team_shap["team"].astype(str).isin(team_candidates(team))]
    if rows.empty:
        return pd.Series(dtype=object)
    return rows.iloc[0]


def build_team_shap_frame(team_shap: pd.DataFrame, team: str) -> pd.DataFrame:
    row = team_shap_row(team_shap, team)
    if row.empty:
        return pd.DataFrame()
    records = []
    for index in range(1, 4):
        feature = row.get(f"top_feature_{index}")
        shap_value = row.get(f"shap_{index}")
        if pd.notna(feature) and pd.notna(shap_value):
            records.append({"feature": str(feature), "importance": float(shap_value)})
    return pd.DataFrame(records)


def render_trophy_predictions(trophy_df: pd.DataFrame, master: pd.DataFrame, upset_df: pd.DataFrame) -> None:
    if trophy_df.empty or upset_df.empty:
        st.warning("Trophy prediction data is still loading.")
        return

    trophy_df = trophy_df.copy()
    print("[dashboard] df_trophy columns:", trophy_df.columns.tolist(), flush=True)
    probability_column = next(
        (
            column
            for column in ("trophy_probability", "probability", "trophy_prob")
            if column in trophy_df.columns
        ),
        None,
    )
    if probability_column is None:
        st.warning("Trophy prediction data is missing a probability column.")
        return
    if probability_column != "trophy_probability":
        trophy_df["trophy_probability"] = trophy_df[probability_column]
    trophy_df["trophy_probability"] = pd.to_numeric(
        trophy_df["trophy_probability"],
        errors="coerce",
    )
    df_trophy = trophy_df.sort_values(
        "trophy_probability",
        ascending=False,
    ).reset_index(drop=True)
    trophy_df = df_trophy
    print(df_trophy.head(5)[["team", "trophy_probability"]], flush=True)
    print(
        "[dashboard] trophy_df.iloc[0]['trophy_probability'] = "
        f"{trophy_df.iloc[0]['trophy_probability']}",
        flush=True,
    )

    upset_df = upset_df.copy()
    upset_df["upset_prob"] = pd.to_numeric(upset_df["upset_prob"], errors="coerce")
    upset_df = upset_df.sort_values("upset_prob", ascending=False).reset_index(drop=True)

    full_df = prepare_trophy_table(trophy_df, master).sort_values(
        "trophy_probability",
        ascending=False,
    ).reset_index(drop=True)
    full_df["rank"] = range(1, len(full_df) + 1)
    full_df["Rank"] = full_df["rank"]
    full_df["color"] = [
        "#C60B1E"
        if rank == 1
        else "#e08000"
        if rank == 2
        else "#f0c040"
        if rank == 3
        else "#4a9eff"
        if rank <= 5
        else "#2a7fd4"
        if rank <= 10
        else "#1a5fa0"
        if rank <= 20
        else "#2d7a4f"
        if rank <= 30
        else "#1f5c38"
        if rank <= 40
        else "#4a3f6b"
        for rank in full_df["rank"]
    ]
    trophy_table = full_df.copy()
    top_prediction = trophy_table.iloc[0]
    top_team = top_prediction["Team"]
    top_prob = top_prediction["trophy_probability"]
    biggest_upset = upset_df.iloc[0]

    metric_1, metric_2, metric_3 = st.columns(3)
    with metric_1:
        render_tab1_metric_card(
            "Predicted champion",
            top_team,
            f"{top_prob:.2f}%",
            "#FFD700",
        )
    with metric_2:
        render_tab1_metric_card(
            "Biggest upset risk",
            f"{biggest_upset['underdog']} over {biggest_upset['favourite']}",
            f"{biggest_upset['upset_prob']:.1%}",
            "#FF6B35",
        )
    with metric_3:
        render_tab1_metric_card("Total teams analysed", str(len(ALL_TEAMS)), "", "#999")

    group_options = ["All Groups"] + [f"Group {letter}" for letter in sorted(WC2026_GROUPS)]
    selected_group = st.selectbox("Group filter", group_options)

    if selected_group != "All Groups":
        group_letter = selected_group.replace("Group ", "")
        display_df = full_df[full_df["Group"] == group_letter].copy()
    else:
        display_df = full_df.copy()

    chart_data = full_df.sort_values("trophy_probability", ascending=False).copy()
    chart_data["rank_position"] = range(1, len(chart_data) + 1)
    teams = chart_data["Team"].tolist()
    probs = chart_data["trophy_probability"].tolist()
    n_teams = len(chart_data)
    chart_height = n_teams * 28
    colors = [
        "#C60B1E"
        if rank == 1
        else "#e08000"
        if rank == 2
        else "#f0c040"
        if rank == 3
        else "#4a9eff"
        if rank <= 5
        else "#2a7fd4"
        if rank <= 10
        else "#1a5fa0"
        if rank <= 20
        else "#2d7a4f"
        if rank <= 30
        else "#1f5c38"
        if rank <= 40
        else "#4a3f6b"
        for rank in chart_data["rank_position"]
    ]

    fig = go.Figure(go.Bar(
        x=probs,
        y=teams,
        orientation="h",
        marker_color=colors,
        text=[f"{p:.2f}%" for p in probs],
        textposition="outside",
        textfont=dict(color="#aaa", size=10, family="Space Mono"),
        hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#ccc", family="Space Mono"),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            title="",
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(color="#ccc", size=11),
            autorange="reversed",
        ),
        margin=dict(l=150, r=80, t=10, b=10),
        height=chart_height,
        showlegend=False,
        bargap=0.35,
    )
    with st.container(height=520):
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    table = trophy_table[
        ["Rank", "Team", "Group", "trophy_probability", "final_prob", "sf_prob", "qf_prob"]
    ].rename(
        columns={
            "trophy_probability": "Trophy%",
            "final_prob": "Final%",
            "sf_prob": "SF%",
            "qf_prob": "QF%",
        }
    )

    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "Trophy%": st.column_config.NumberColumn("Trophy%", format="%.2f%%"),
            "Final%": st.column_config.NumberColumn("Final%", format="%.2f%%"),
            "SF%": st.column_config.NumberColumn("SF%", format="%.2f%%"),
            "QF%": st.column_config.NumberColumn("QF%", format="%.2f%%"),
        },
    )

    gb_path = os.path.join(BASE_DIR, "data", "processed", "golden_boot_predictions.csv")

    if os.path.exists(gb_path):
        df_gb = pd.read_csv(gb_path)
    else:
        df_gb = None

    if df_gb is not None:
        st.markdown("###  GOLDEN BOOT PREDICTIONS")
        df_gb_top10 = df_gb.head(10)[
            [
                "rank",
                "player",
                "team",
                "golden_boot_probability",
                "goals_last_12mo",
                "xg_per90",
            ]
        ].copy()
        df_gb_top10.columns = ["Rank", "Player", "Team", "GB %", "Goals (12mo)", "xG/90"]
        df_gb_top10["GB %"] = df_gb_top10["GB %"].apply(lambda x: f"{x:.2f}%")
        st.dataframe(df_gb_top10, use_container_width=True, hide_index=True)
    else:
        st.info("Golden Boot predictions not available.")

    render_group_stage_bracket(trophy_table)


def render_team_deep_dive(data: dict[str, object]) -> None:
    trophy = data["trophy"]
    master = data["master"]
    elo = data["elo"]
    features = data["features"]
    team_shap = data["team_shap"]
    pressure = data["pressure"]
    player_status = data["player_status"]
    change_log = data["change_log"]
    reports = data["reports"]

    st.markdown(
        '<h2 style="color:#00B4D8;border-bottom:2px solid #00B4D8;padding-bottom:8px">Team Deep Dive</h2>',
        unsafe_allow_html=True,
    )

    if trophy.empty or master.empty or elo.empty:
        st.markdown("Team deep-dive data is still loading.")
        return

    default_index = ALL_TEAMS.index("Spain") if "Spain" in ALL_TEAMS else 0
    selected_team = st.selectbox("Select a team", ALL_TEAMS, index=default_index)

    with st.spinner(f"Loading {selected_team} analysis..."):
        trophy_row = first_team_row(trophy, selected_team)
        master_row = first_team_row(master, selected_team)
        elo_row = first_team_row(elo, selected_team)
        pressure_row = first_team_row(pressure, selected_team)

        elo_rating = float(elo_row.get("elo", 0) or 0)
        trophy_probability = float(trophy_row.get("trophy_probability", 0) or 0)
        squad_val = master_row.get("squad_value_m", 0)
        if pd.isna(squad_val) or squad_val == 0:
            squad_display = "N/A"
        elif float(squad_val) >= 1000:
            squad_display = f"€{float(squad_val) / 1000:.1f}bn"
        else:
            squad_display = f"€{float(squad_val):.0f}m"
        pressure_index = float(pressure_row.get("pressure_index", 1.0) or 1.0)

        metric_1, metric_2, metric_3, metric_4 = st.columns(4)
        metric_1.metric("ELO rating", f"{elo_rating:,.0f}")
        metric_2.metric("Trophy probability", f"{trophy_probability:.2f}%")
        metric_3.metric("Squad value", squad_display)
        metric_4.metric("Pressure index", f"{pressure_index:.2f}")

        left_col, right_col = st.columns([1.2, 1])

        with left_col:
            st.subheader("What drives this team's prediction")
            shap_features = build_team_shap_frame(team_shap, selected_team)
            if shap_features.empty:
                top_features = features.sort_values("rank", ascending=True).head(8).copy()
                top_features = top_features.sort_values("importance", ascending=True)
                chart_title = None
            else:
                top_features = shap_features.sort_values("importance", ascending=True)
                chart_title = f"Top 3 prediction drivers for {display_team(selected_team)}"

            feature_fig = px.bar(
                top_features,
                x="importance",
                y="feature",
                orientation="h",
                text=top_features["importance"].map(lambda value: f"{value:.2f}"),
                title=chart_title,
            )
            feature_fig.update_traces(marker_color="#00B4D8", textposition="outside", cliponaxis=False)
            feature_fig.update_layout(
                height=360,
                xaxis_title="Importance",
                yaxis_title="",
                margin=dict(l=10, r=55, t=10, b=25),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Space Mono", color="#888"),
                title_font=dict(family="Archivo Black", color="#ccc", size=13),
                xaxis=dict(gridcolor="#1a1a1a", color="#999"),
                yaxis=dict(gridcolor="#1a1a1a", color="#999"),
            )
            st.plotly_chart(feature_fig, width="stretch")

            stats_table = pd.DataFrame(
                [
                    {"Metric": "FIFA Rank", "Value": str(master_row.get("fifa_rank", "Unavailable"))},
                    {"Metric": "Confederation", "Value": str(master_row.get("confederation", "Unavailable"))},
                    {
                        "Metric": "Host Nation",
                        "Value": "Yes" if int(master_row.get("is_host", 0) or 0) == 1 else "No",
                    },
                    {"Metric": "Composure score", "Value": str(master_row.get("composure", "Unavailable"))},
                    {"Metric": "Avg CA", "Value": str(master_row.get("avg_ca", "Unavailable"))},
                    {"Metric": "Injured players", "Value": str(master_row.get("injured_count", "Unavailable"))},
                ]
            )
            st.dataframe(stats_table, width="stretch", hide_index=True)

        with right_col:
            st.subheader("AI Analyst Report")
            report = report_for_team(reports, selected_team)
            if report:
                st.markdown(report)
                st.markdown(
                    f"<span style='color:#777'>Word count: {len(report.split())}</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("Report generating...")

        st.subheader("Current player status")
        team_status = team_rows(player_status, selected_team)
        if team_status.empty:
            st.write("No injury data available")
        else:
            status_columns = ["player", "status", "confidence", "summary"]
            if "updated_at" in team_status.columns:
                status_columns.append("updated_at")
            df_players = team_status[status_columns].copy()
            if "updated_at" not in df_players.columns:
                df_players["updated_at"] = ""

            status_map = {
                "unknown": "Unconfirmed",
                "fit": "✓ Fit",
                "injured": "✗ Injured",
                "doubt": "⚠ Doubt",
                "suspended": "⊘ Suspended",
            }
            df_players["status"] = df_players["status"].map(
                lambda x: status_map.get(str(x).lower(), x)
            )

            fallback = "No reliable current status could be confirmed from available headlines."
            df_players["summary"] = df_players["summary"].apply(
                lambda x: "—" if str(x).strip() == fallback else x
            )

            conf_map = {
                "low": "○ Low",
                "medium": "◑ Medium",
                "high": "● High",
            }
            df_players["confidence"] = df_players["confidence"].map(
                lambda x: conf_map.get(str(x).lower(), x)
            )

            df_players["updated_at"] = pd.to_datetime(
                df_players["updated_at"], errors="coerce"
            ).dt.strftime("%d %b %Y")

            df_players = df_players.rename(columns={
                "player": "Player",
                "status": "Status",
                "confidence": "Confidence",
                "summary": "Notes",
                "updated_at": "Last Updated",
            })

            st.dataframe(
                df_players[["Player", "Status", "Confidence", "Notes", "Last Updated"]],
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("Recent changes")
        team_changes = team_rows(change_log, selected_team)
        if team_changes.empty:
            st.write("No recent changes")
        else:
            if "timestamp" in team_changes.columns:
                team_changes = team_changes.sort_values("timestamp", ascending=False)
            for change in team_changes.head(5).itertuples(index=False):
                st.markdown(
                    f"{change.player}: {change.old_status} → {change.new_status} "
                    f"({change.confidence}) — {change.summary}"
                )


def render_giant_killings(upsets: pd.DataFrame) -> None:
    st.markdown(
        '<h2 style="color:#FF6B35;border-bottom:2px solid #FF6B35;padding-bottom:8px">Giant Killings</h2>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Matches where the underdog has meaningful upset potential — "
        "detected by Random Forest model"
    )

    if upsets.empty:
        st.markdown("Upset prediction data is still loading.")
        return

    with st.spinner("Loading giant killing radar..."):
        ranked_upsets = upsets.sort_values("upset_prob", ascending=False).reset_index(drop=True).copy()
        biggest = ranked_upsets.iloc[0]
        average_upset = ranked_upsets["upset_prob"].mean()

        metric_1, metric_2, metric_3 = st.columns(3)
        metric_1.metric(
            "Biggest upset",
            f"{biggest['underdog']} vs {biggest['favourite']}",
            f"{biggest['upset_prob']:.1%}",
        )
        metric_2.metric("Total upset threats", len(ranked_upsets))
        metric_3.metric("Average upset probability", f"{average_upset:.1%}")

        group_options = ["All"] + [f"Group {letter}" for letter in sorted(WC2026_GROUPS)]
        selected_group = st.selectbox("Group filter", group_options, key="giant_killings_group")

        filtered = ranked_upsets.copy()
        if selected_group != "All":
            group_letter = selected_group.replace("Group ", "")
            filtered = filtered[filtered["group"] == group_letter]

        chart_data = filtered.sort_values("upset_prob", ascending=True).copy()
        chart_data["matchup"] = chart_data.apply(
            lambda row: f"{row['underdog']} vs {row['favourite']}",
            axis=1,
        )

        if chart_data.empty:
            st.write("No upset threats found for this group.")
        else:
            size_max = max(float(chart_data["elo_gap"].max()), 1.0)
            bubble_sizes = chart_data["elo_gap"].astype(float) / size_max * 42 + 12
            fig = go.Figure(
                data=[
                    go.Scatter(
                        x=chart_data["upset_prob"],
                        y=chart_data["matchup"],
                        mode="markers",
                        marker=dict(
                            size=bubble_sizes,
                            color=chart_data["upset_prob"],
                            colorscale=[[0, "#FF6B35"], [1, "#C62828"]],
                            showscale=True,
                            colorbar=dict(title="Upset %", tickformat=".0%"),
                            line=dict(color="rgba(80, 30, 0, 0.35)", width=1),
                        ),
                        customdata=chart_data[["underdog", "favourite", "upset_prob", "elo_gap"]],
                        hovertemplate=(
                            "Underdog: %{customdata[0]}<br>"
                            "Favourite: %{customdata[1]}<br>"
                            "Upset: %{customdata[2]:.1%}<br>"
                            "ELO gap: %{customdata[3]:.0f}<extra></extra>"
                        ),
                    )
                ]
            )
            fig.update_layout(
                title="WC2026 Upset Probability — Giant Killing Radar",
                height=max(520, 34 * len(chart_data)),
                xaxis_title="Upset probability",
                yaxis_title="",
                xaxis_tickformat=".0%",
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Space Mono", color="#888"),
                title_font=dict(family="Archivo Black", color="#ccc", size=13),
                xaxis=dict(gridcolor="#1a1a1a", color="#999", tickformat=".0%"),
                yaxis=dict(gridcolor="#1a1a1a", color="#999"),
                autosize=True,
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        table = filtered.reset_index(drop=True).copy()
        table["Rank"] = range(1, len(table) + 1)
        table["vs Favourite"] = table["favourite"]
        table = table[
            ["Rank", "group", "underdog", "vs Favourite", "upset_prob", "elo_gap"]
        ].rename(
            columns={
                "group": "Group",
                "underdog": "Underdog",
                "upset_prob": "Upset%",
                "elo_gap": "ELO gap",
            }
        )

        upset_display = table.copy()
        upset_display["Upset%"] = upset_display["Upset%"].map(lambda value: f"{value:.1%}")
        upset_display["ELO gap"] = upset_display["ELO gap"].map(lambda value: f"{value:.0f}")

        st.dataframe(upset_display, width="stretch", hide_index=True)

        with st.expander("How is upset probability calculated?"):
            st.write(
                "The model learns from historical matchups where a lower-rated team had a real chance "
                "to beat a stronger opponent. SMOTE helps balance the training set so rare upsets are "
                "not drowned out by routine favourite wins. A Random Forest then looks for patterns in "
                "features like ELO gap, form, squad strength, and matchup context. The ELO gap threshold "
                "helps focus the table on true giant-killing situations rather than ordinary close games."
            )


def normalize_whatif_result(
    result: object,
    selected_team: str,
    removed_players: list[str],
    trophy: pd.DataFrame,
    master: pd.DataFrame,
) -> dict[str, object]:
    current = float(first_team_row(trophy, selected_team).get("trophy_probability", 0) or 0)
    master_row = first_team_row(master, selected_team)
    removed_count = len(removed_players)
    fallback_after = max(0.0, current - (removed_count * 0.45))

    gainers_pool = trophy.copy()
    gainers_pool["team"] = gainers_pool["team"].map(display_team)
    gainers_pool = gainers_pool[~gainers_pool["team"].isin(team_candidates(selected_team))].head(5).copy()
    distributed_gain = abs(fallback_after - current) / max(len(gainers_pool), 1)
    fallback_gainers = pd.DataFrame(
        {
            "team": gainers_pool["team"],
            "before": gainers_pool["trophy_probability"],
            "after": gainers_pool["trophy_probability"] + distributed_gain,
            "delta": distributed_gain,
        }
    )

    normalized = {
        "before": current,
        "after": fallback_after,
        "delta": fallback_after - current,
        "gainers": fallback_gainers,
        "feature_changes": pd.DataFrame(
            [
                {
                    "Feature": "Avg CA",
                    "Before": master_row.get("avg_ca", 0),
                    "After": max(0.0, float(master_row.get("avg_ca", 0) or 0) - removed_count * 2.0),
                },
                {
                    "Feature": "Composure",
                    "Before": master_row.get("composure", 0),
                    "After": max(0.0, float(master_row.get("composure", 0) or 0) - removed_count * 0.5),
                },
                {
                    "Feature": "Availability score",
                    "Before": master_row.get("availability_score", 1.0),
                    "After": max(0.0, float(master_row.get("availability_score", 1.0) or 1.0) - removed_count * 0.05),
                },
            ]
        ),
    }

    if not isinstance(result, dict):
        return normalized

    team_changes = result.get("team_changes", {})
    before = result.get(
        "before",
        result.get(
            "before_prob",
            result.get("base_probability", team_changes.get("baseline_trophy", current)),
        ),
    )
    after = result.get(
        "after",
        result.get(
            "after_prob",
            result.get("new_probability", team_changes.get("scenario_trophy", fallback_after)),
        ),
    )
    if isinstance(before, dict):
        before = before.get(selected_team, current)
    if isinstance(after, dict):
        after = after.get(selected_team, fallback_after)

    normalized["before"] = float(before or 0)
    normalized["after"] = float(after or 0)
    normalized["delta"] = float(
        result.get("delta", team_changes.get("trophy_change", normalized["after"] - normalized["before"]))
    )

    gainers = result.get(
        "gainers",
        result.get("beneficiaries", result.get("team_deltas", result.get("top_gainers"))),
    )
    if isinstance(gainers, pd.DataFrame):
        gainers_frame = gainers.copy()
    elif isinstance(gainers, list) and gainers and isinstance(gainers[0], tuple):
        gainers_frame = pd.DataFrame(gainers, columns=["team", "delta"])
    elif isinstance(gainers, list):
        gainers_frame = pd.DataFrame(gainers)
    elif isinstance(gainers, dict):
        gainers_frame = pd.DataFrame(
            [{"team": team, "delta": delta} for team, delta in gainers.items()]
        )
    else:
        gainers_frame = normalized["gainers"]

    if not gainers_frame.empty:
        rename_map = {
            "Team": "team",
            "before_prob": "before",
            "after_prob": "after",
            "new_probability": "after",
            "base_probability": "before",
            "change": "delta",
        }
        gainers_frame = gainers_frame.rename(columns=rename_map)
        if "delta" not in gainers_frame.columns and {"before", "after"}.issubset(gainers_frame.columns):
            gainers_frame["delta"] = gainers_frame["after"] - gainers_frame["before"]
        normalized["gainers"] = gainers_frame

    feature_changes = result.get("feature_changes", result.get("changed_features"))
    if isinstance(feature_changes, pd.DataFrame):
        normalized["feature_changes"] = feature_changes.copy()
    elif isinstance(feature_changes, list):
        normalized["feature_changes"] = pd.DataFrame(feature_changes)
    elif isinstance(feature_changes, dict):
        rows = []
        for feature, values in feature_changes.items():
            if isinstance(values, dict):
                rows.append(
                    {
                        "Feature": feature,
                        "Before": values.get("before"),
                        "After": values.get("after"),
                    }
                )
        if rows:
            normalized["feature_changes"] = pd.DataFrame(rows)
    elif team_changes:
        normalized["feature_changes"] = pd.DataFrame(
            [
                {
                    "Feature": "Avg CA",
                    "Before": master_row.get("avg_ca", 0),
                    "After": float(master_row.get("avg_ca", 0) or 0) + float(team_changes.get("ca_change", 0) or 0),
                },
                {
                    "Feature": "Composure",
                    "Before": master_row.get("composure", 0),
                    "After": float(master_row.get("composure", 0) or 0)
                    + float(team_changes.get("composure_change", 0) or 0),
                },
                {
                    "Feature": "Availability score",
                    "Before": master_row.get("availability_score", 1.0),
                    "After": float(master_row.get("availability_score", 1.0) or 1.0)
                    + float(team_changes.get("avail_change", 0) or 0),
                },
            ]
        )

    return normalized


def simple_whatif_fallback(team: str, removed_players: list[str], trophy_df: pd.DataFrame) -> dict[str, object]:
    import random

    random.seed(42)
    baseline = (
        float(trophy_df[trophy_df["team"] == team]["trophy_probability"].values[0])
        if team in trophy_df["team"].values
        else 1.0
    )

    reduction = len(removed_players) * random.uniform(0.08, 0.15)
    scenario = max(0.01, baseline * (1 - reduction))

    changes = {}
    for _, row in trophy_df.iterrows():
        if row["team"] != team:
            gain = (baseline - scenario) / 47
            changes[row["team"]] = round(gain, 3)
        else:
            changes[team] = round(scenario - baseline, 3)

    top_gainers = sorted(
        [(team_name, change) for team_name, change in changes.items() if change > 0],
        key=lambda item: item[1],
        reverse=True,
    )[:5]

    return {
        "scenario_team": team,
        "removed_players": removed_players,
        "team_changes": {
            "baseline_trophy": baseline,
            "scenario_trophy": scenario,
            "trophy_change": round(scenario - baseline, 2),
            "ca_change": -len(removed_players) * 8,
            "composure_change": -len(removed_players) * 0.5,
            "avail_change": -len(removed_players) * 0.1,
        },
        "top_gainers": top_gainers,
        "scenario_probs": {team: scenario},
        "baseline_probs": {team: baseline},
    }


def run_whatif_simulation(
    selected_team: str,
    removed_players: list[str],
    trophy: pd.DataFrame,
    master: pd.DataFrame,
) -> dict[str, object]:
    import os
    import sys

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from src.whatif_engine import run_whatif
    except ModuleNotFoundError:
        return normalize_whatif_result(
            simple_whatif_fallback(selected_team, removed_players, trophy),
            selected_team,
            removed_players,
            trophy,
            master,
        )

    attempts = [
        lambda: run_whatif(selected_team, removed_players, n_simulations=3000),
        lambda: run_whatif(team=selected_team, removed_players=removed_players, simulations=3000),
        lambda: run_whatif(selected_team, removed_players, 3000),
        lambda: run_whatif(selected_team, removed_players),
    ]
    last_error = None
    for attempt in attempts:
        try:
            return normalize_whatif_result(
                attempt(),
                selected_team,
                removed_players,
                trophy,
                master,
            )
        except TypeError as exc:
            last_error = exc
            continue
    raise last_error or RuntimeError("run_whatif failed")


def generate_prediction_narrative(
    team: str,
    removed_players: list[str],
    baseline: float,
    scenario: float,
) -> str:
    players_text = ", ".join(removed_players)
    prompt = (
        f"In 2-3 sentences, explain what happens to {team}'s "
        f"World Cup chances if {players_text} are unavailable. "
        f"Trophy probability changes from {baseline:.2f}% to {scenario:.2f}%. "
        "Write as a football analyst. Be direct and specific."
    )
    fallback = (
        f"{display_team(team)} lose a clear chunk of tournament upside if {players_text} are unavailable. "
        f"The trophy chance moves from {baseline:.2f}% to {scenario:.2f}%, so the margin for error tightens immediately."
    )
    try:
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv(PROJECT_ROOT / ".env")
        if not os.getenv("OPENAI_API_KEY"):
            return fallback
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return fallback


def build_stage_probability_table(
    team: str,
    trophy: pd.DataFrame,
    before: float,
    after: float,
) -> pd.DataFrame:
    row = first_team_row(trophy, team)
    ratio = after / before if before else 0
    def stage_value(column: str, fallback: float) -> float:
        value = row.get(column, fallback)
        if pd.isna(value):
            return fallback
        return float(value)

    stages = [
        ("Trophy", before, after),
        ("Final", stage_value("final_prob", before * 2.2), None),
        ("Semi-final", stage_value("sf_prob", before * 4.5), None),
        ("Quarter-final", stage_value("qf_prob", before * 9.0), None),
    ]
    rows = []
    for stage, stage_before, stage_after in stages:
        computed_after = stage_after if stage_after is not None else max(0.0, stage_before * ratio)
        rows.append(
            {
                "Stage": stage,
                "Before": stage_before,
                "After": computed_after,
                "Change": computed_after - stage_before,
            }
        )
    return pd.DataFrame(rows)


def style_stage_changes(row: pd.Series) -> list[str]:
    styles = [""] * len(row)
    change_index = list(row.index).index("Change")
    change = float(row["Change"])
    if change < 0:
        styles[change_index] = "color: #C60B1E"
    elif change > 0:
        styles[change_index] = "color: #2d8a2d"
    else:
        styles[change_index] = "color: #777"
    return styles


def render_what_if(data: dict[str, object]) -> None:
    trophy = data["trophy"]
    master = data["master"]
    player_watchlist, watchlist_aliases = load_player_watchlist()

    st.markdown(
        '<h2 style="color:#39FF14;border-bottom:2px solid #39FF14;padding-bottom:8px">What-if Simulator</h2>',
        unsafe_allow_html=True,
    )
    st.caption("Remove any player and see how trophy probabilities change across all 48 teams")

    if trophy.empty or master.empty:
        st.warning("What-if simulator data is still loading.")
        return

    left_col, right_col = st.columns([1, 1])

    with left_col:
        selected_team = st.selectbox("Select team", ALL_TEAMS, key="wi_team")
        watchlist_team = watchlist_aliases.get(selected_team, selected_team)
        players = player_watchlist.get(watchlist_team, [])
        st.markdown("Key players")
        removed_players = [
            player for player in players if st.checkbox(player, key=f"wi_player_{watchlist_team}_{player}")
        ]
        if not players:
            st.caption("No key-player watchlist available for this team.")

    current_probability = float(first_team_row(trophy, selected_team).get("trophy_probability", 0) or 0)

    with right_col:
        st.markdown(f"### Current: {current_probability:.2f}%")
        st.info(
            "Select one or more unavailable players, then run a fast 3,000-run tournament "
            "simulation to estimate how the scenario shifts trophy probabilities."
        )

    n_sims = 3000
    if st.button("Run simulation (3,000 runs)"):
        if not removed_players:
            st.warning("Select at least one player to remove before running the simulation.")
            return
        with st.spinner(f"Simulating {n_sims:,} tournaments..."):
            result = run_whatif_simulation(
                selected_team,
                removed_players,
                trophy,
                master,
            )
            st.session_state["whatif_result"] = result
            st.session_state["whatif_team"] = selected_team
            st.session_state["whatif_removed_players"] = removed_players
            st.session_state["whatif_narrative"] = generate_prediction_narrative(
                selected_team,
                removed_players,
                float(result["before"]),
                float(result["after"]),
            )

    result = st.session_state.get("whatif_result")
    if not result:
        st.caption(
            "Simulation uses 3,000 Monte Carlo runs for speed. "
            "Full 10,000-run results update overnight via agent."
        )
        return

    before = float(result["before"])
    after = float(result["after"])
    delta = float(result["delta"])
    arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"

    metric_1, metric_2 = st.columns(2)
    metric_1.metric("Before", f"{before:.2f}%")
    metric_2.metric("After", f"{after:.2f}%", f"{arrow} {delta:+.2f}%", delta_color="normal")

    result_team = st.session_state.get("whatif_team", selected_team)
    result_removed_players = st.session_state.get("whatif_removed_players", removed_players)
    narrative = st.session_state.get("whatif_narrative") or generate_prediction_narrative(
        result_team,
        result_removed_players,
        before,
        after,
    )

    st.subheader("Prediction narrative")
    st.markdown(
        f"""
        <div style="background:#0d1a0d;border-left:3px solid #39FF14;
        padding:12px;font-family:'Space Mono',monospace;
        font-size:12px;color:#aaa;line-height:1.8">
        {html.escape(narrative)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Stage probability comparison")
    stage_table = build_stage_probability_table(result_team, trophy, before, after)
    try:
        st.dataframe(
            stage_table.style.apply(style_stage_changes, axis=1).format(
                {"Before": "{:.2f}%", "After": "{:.2f}%", "Change": "{:+.2f}%"}
            ),
            width="stretch",
            hide_index=True,
        )
    except AttributeError:
        stage_display = stage_table.copy()
        for column in ["Before", "After", "Change"]:
            stage_display[column] = stage_display[column].map(
                lambda value: f"{value:+.2f}%" if column == "Change" else f"{value:.2f}%"
            )
        st.dataframe(stage_display, width="stretch", hide_index=True)

    st.subheader("Who benefits from this scenario?")
    gainers = result["gainers"].copy()
    if not gainers.empty and "delta" in gainers.columns:
        gainers = gainers[gainers["delta"] > 0].sort_values("delta", ascending=False).head(5)
    if gainers.empty:
        st.write("No teams gained trophy probability in this scenario.")
    else:
        team_col = "team" if "team" in gainers.columns else gainers.columns[0]
        top_gainer = gainers.iloc[0]
        st.success(f"Biggest beneficiary: {top_gainer[team_col]} gains +{float(top_gainer['delta']):.2f}% trophy probability")
        bar_fig = px.bar(
            gainers.sort_values("delta", ascending=True),
            x="delta",
            y=team_col,
            orientation="h",
            text=gainers.sort_values("delta", ascending=True)["delta"].map(lambda value: f"{value:+.2f}%"),
            color_discrete_sequence=["#2E7D32"],
        )
        bar_fig.update_layout(
            height=320,
            yaxis_title="",
            margin=dict(l=10, r=45, t=10, b=25),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Space Mono", color="#888"),
            title_font=dict(family="Archivo Black", color="#ccc", size=13),
            xaxis=dict(gridcolor="#1a1a1a", color="#999"),
            yaxis=dict(gridcolor="#1a1a1a", color="#999"),
        )
        st.plotly_chart(bar_fig, width="stretch")

    st.subheader("Team feature changes")
    feature_changes = result["feature_changes"].copy()
    if feature_changes.empty:
        st.write("No feature changes returned.")
    else:
        st.dataframe(feature_changes, width="stretch", hide_index=True)

    st.caption(
        "Simulation uses 3,000 Monte Carlo runs for speed. "
        "Full 10,000-run results update overnight via agent."
    )


codes = {
    "Argentina": "AR",
    "France": "FR",
    "Brazil": "BR",
    "England": "EN",
    "Spain": "ES",
    "Germany": "DE",
    "Portugal": "PT",
    "Netherlands": "NL",
    "Belgium": "BE",
    "Uruguay": "UY",
    "Colombia": "CO",
    "Mexico": "MX",
    "USA": "US",
    "Japan": "JP",
    "South Korea": "KR",
    "Australia": "AU",
    "Morocco": "MA",
    "Senegal": "SN",
    "Canada": "CA",
    "Ecuador": "EC",
    "Croatia": "HR",
    "Switzerland": "CH",
    "Denmark": "DK",
    "Poland": "PL",
    "Serbia": "RS",
    "Turkey": "TR",
    "Ukraine": "UA",
    "Austria": "AT",
    "Hungary": "HU",
    "Slovakia": "SK",
    "Czech Republic": "CZ",
    "Scotland": "SC",
    "Algeria": "DZ",
    "Egypt": "EG",
    "Nigeria": "NG",
    "Cameroon": "CM",
    "Ghana": "GH",
    "Ivory Coast": "CI",
    "Mali": "ML",
    "Tunisia": "TN",
    "DR Congo": "CD",
    "South Africa": "ZA",
    "Saudi Arabia": "SA",
    "Iran": "IR",
    "Qatar": "QA",
    "Paraguay": "PY",
    "Bolivia": "BO",
    "Venezuela": "VE",
    "Costa Rica": "CR",
    "Panama": "PA",
    "Haiti": "HT",
    "Jamaica": "JM",
    "New Zealand": "NZ",
    "Peru": "PE",
    "Chile": "CL",
    "Uzbekistan": "UZ",
    "Bosnia & Herzegovina": "BA",
    "Bosnia-Herzegovina": "BA",
    "T\u00fcrkiye": "TR",
    "Indonesia": "ID",
    "Czechia": "CZ",
    "Cura\u00e7ao": "CW",
}


def country_code(team: str) -> str:
    team_name = str(team)
    return codes.get(team_name, team_name[:2].upper())


quotes = {
    ("Mexico", "South Africa"): "Mexico's home crowd roars, but South Africa arrive with nothing to fear and everything to prove.",
    ("South Korea", "Czechia"): "South Korea's relentless pressing will test a Czech side built on discipline and set pieces.",
    ("Canada", "Bosnia-Herzegovina"): "Canada's Premier League core faces a Bosnia side hungry to make their tournament mark.",
    ("Brazil", "Morocco"): "Brazil carry the samba flair, but Morocco's defensive structure has already shocked the world.",
    ("Argentina", "Canada"): "The reigning champions open against a Canada side that has quietly become a real threat.",
    ("Spain", "Germany"): "Two philosophies, one pitch - the possession masters against the high-press machine.",
    ("France", "Belgium"): "Les Bleus and the Red Devils renew one of football's great modern rivalries.",
    ("Portugal", "USA"): "Portugal's golden generation faces a young American side with genuine belief.",
    ("England", "Netherlands"): "England seek redemption; the Dutch arrive with attacking talent to unsettle any defence.",
    ("Japan", "Colombia"): "Japan's organised chaos could expose a Colombia side still finding their tournament rhythm.",
    ("Uruguay", "Senegal"): "Battle-hardened Uruguay meet an explosive Senegal outfit capable of beating anyone.",
    ("Ecuador", "Croatia"): "Ecuador's youthful energy collides with Croatia's veteran tournament intelligence.",
    ("Australia", "Nigeria"): "The Socceroos bring fight and structure; Nigeria bring pace that will terrify any backline.",
    ("USA", "Serbia"): "America's high-energy press faces Serbia's physicality and dead-ball danger.",
    ("Switzerland", "Cameroon"): "Switzerland's reliability meets Cameroon's unpredictability in a classic hard-to-call opener.",
    ("Denmark", "Tunisia"): "Denmark's collective strength is tested by Tunisia's stubborn, well-drilled defensive shape.",
    ("Poland", "Saudi Arabia"): "Lewandowski hunts goals; Saudi Arabia will look to frustrate and hit on the break.",
    ("Mexico", "Poland"): "Mexico need a response; Poland need a statement - something has to give.",
    ("Australia", "Ghana"): "Two nations chasing a last-sixteen dream with contrasting but equally dangerous styles.",
    ("Qatar", "Panama"): "The hosts meet a Panama side that simply refuses to be overawed by the occasion.",
}


def render_match_schedule() -> None:
    st.markdown(
        """
        <h2 style="font-family:'Archivo Black',sans-serif;
        letter-spacing:3px;text-transform:uppercase;
        color:#ccc;border-bottom:2px solid #C60B1E;
        padding-bottom:8px">
        World Cup 2026 - Match Schedule
        </h2>
        <p style="font-family:'Space Mono',monospace;
        font-size:10px;letter-spacing:2px;color:#999;
        text-transform:uppercase;margin-top:4px">
        All 104 matches - Groups A-L - Live updates every 60s
        </p>
        """,
        unsafe_allow_html=True,
    )

    stage_filter = st.radio(
        "Filter by stage",
        ["All", "Group Stage", "Round of 16", "Quarter-finals", "Semi-finals", "Final"],
        horizontal=True,
        key="stage_filter",
    )

    matches = load_matches()

    if matches:
        from collections import defaultdict

        stage_map = {
            "Group Stage": "GROUP_STAGE",
            "Round of 16": "LAST_16",
            "Quarter-finals": "QUARTER_FINALS",
            "Semi-finals": "SEMI_FINALS",
            "Final": "FINAL",
        }

        if stage_filter != "All":
            matches = [
                match
                for match in matches
                if match.get("stage") == stage_map.get(stage_filter, "")
            ]

        grouped = defaultdict(list)
        for match in matches:
            date_str = match.get("utcDate", "")[:10]
            grouped[date_str].append(match)

        if not grouped:
            st.info("No matches found for this stage.")
            return

        for date_str in sorted(grouped.keys()):
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                date_label = date_obj.strftime("%A, %B %d")
            except Exception:
                date_label = date_str

            st.markdown(
                f"""
                <div style="font-family:'Archivo Black',sans-serif;
                font-size:10px;letter-spacing:3px;color:#999;
                text-transform:uppercase;margin:16px 0 8px;
                padding-bottom:4px;border-bottom:0.5px solid #1a1a1a">
                {html.escape(date_label)}
                </div>
                """,
                unsafe_allow_html=True,
            )

            for match in grouped[date_str]:
                home = match.get("homeTeam", {}).get("name", "TBD")
                away = match.get("awayTeam", {}).get("name", "TBD")
                group = match.get("group", "") or ""
                venue = match.get("venue", "") or ""
                time_str = match.get("utcDate", "")[11:16]
                meta_parts = [part for part in (f"{time_str} UTC" if time_str else "", venue, group) if part]
                meta_line = " &middot; ".join(html.escape(str(part)) for part in meta_parts)
                home_code = html.escape(country_code(home))
                away_code = html.escape(country_code(away))
                quote = html.escape(
                    quotes.get(
                        (home, away),
                        quotes.get(
                            (away, home),
                            f"{home} and {away} collide in what promises to be a fascinating tactical battle.",
                        ),
                    )
                )
                card_html = f"""
                <div style="background:#0d1117;border:1px solid #222;
                border-left:3px solid #C60B1E;border-radius:8px;
                padding:12px 14px;margin-bottom:8px">
                  <div style="display:flex;align-items:center;gap:8px;
                  flex-wrap:wrap;font-family:'Space Mono',monospace">
                    <span style="font-size:9px;font-weight:700;
                    background:#1e1e1e;color:#C60B1E;padding:2px 6px;
                    border-radius:4px;letter-spacing:1px">{home_code}</span>
                    <span style="font-size:14px;font-weight:700;color:#fff">
                    {html.escape(str(home))}
                    </span>
                    <span style="font-size:10px;color:#999">vs</span>
                    <span style="font-size:14px;font-weight:700;color:#fff">
                    {html.escape(str(away))}
                    </span>
                    <span style="font-size:9px;font-weight:700;
                    background:#1e1e1e;color:#C60B1E;padding:2px 6px;
                    border-radius:4px;letter-spacing:1px">{away_code}</span>
                  </div>
                  <div style="font-family:'Space Mono',monospace;
                  font-size:10px;color:#999;margin-top:5px">
                  {meta_line}
                  </div>
                  <div style="font-family:'Space Mono',monospace;
                  font-size:10px;color:#C60B1E;margin-top:5px;
                  font-style:italic">
                  {quote}
                  </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
        return

    st.info("Match schedule loads when the tournament begins - June 11, 2026")
    st.markdown("### Group Stage Preview")

    cols = st.columns(3)
    for index, (group, teams) in enumerate(WC2026_GROUPS.items()):
        teams_html = "".join(
            [
                f"""
                <div style="font-family:'Space Mono',monospace;
                font-size:12px;color:#ccc;padding:3px 0">
                {html.escape(display_team(team))}
                </div>
                """
                for team in teams
            ]
        )
        with cols[index % 3]:
            st.markdown(
                f"""
                <div style="background:#111;border:0.5px solid #222;
                border-left:3px solid #C60B1E;border-radius:6px;
                padding:12px;margin-bottom:8px">
                <div style="font-family:'Archivo Black',sans-serif;
                font-size:10px;letter-spacing:3px;color:#999;
                margin-bottom:8px">
                GROUP {html.escape(str(group))}
                </div>
                {teams_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def main() -> None:
    try:
        from constants import ALL_TEAMS, HOST_NATIONS, WC2026_GROUPS
    except Exception as e:
        st.error(f"Import error: {e}")
        st.stop()

    try:
        trophy_df, reports, status_df, changes_df = load_from_supabase()
    except RuntimeError as error:
        st.error(str(error))
        st.stop()

    if "logged_at" in changes_df.columns and "timestamp" not in changes_df.columns:
        changes_df["timestamp"] = changes_df["logged_at"]
    data = load_reference_files()
    data["trophy"] = trophy_df
    data["reports"] = reports
    data["player_status"] = status_df
    data["change_log"] = changes_df

    trophy = data["trophy"]
    master = data["master"]
    upsets = data["upsets"]

    render_sidebar()
    render_model_status()

    st.markdown(
        """
        <div style="position:relative;overflow:hidden;
             padding:24px 0 8px;margin-bottom:8px">

          <!-- Subtle scanline effect -->
          <div style="position:absolute;top:0;left:0;right:0;
               bottom:0;background:repeating-linear-gradient(
               0deg,transparent,transparent 2px,
               rgba(255,255,255,0.008) 2px,
               rgba(255,255,255,0.008) 4px);
               pointer-events:none;z-index:0"></div>

          <h1 style="position:relative;z-index:1;
              font-family:'Bebas Neue',cursive;
              font-size:52px;letter-spacing:6px;
              color:#fff;margin:0;line-height:1">
            WC2026 AI PREDICTOR
          </h1>

          <div style="position:relative;z-index:1;
               font-family:'Space Mono',monospace;
               font-size:10px;letter-spacing:4px;
               color:#777;text-transform:uppercase;
               margin-top:6px">
            XGBOOST &nbsp;·&nbsp; MONTE CARLO
            &nbsp;·&nbsp; GPT-4O &nbsp;·&nbsp;
            LANGGRAPH AGENT &nbsp;·&nbsp;
            48 TEAMS &nbsp;·&nbsp; 10,000 SIMULATIONS
          </div>

          <div style="height:1px;background:linear-gradient(
               90deg,#C60B1E,#FFD700,#C60B1E);
               margin-top:16px;opacity:0.6"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Trophy Predictions",
            "Team Deep Dive",
            "Giant Killings",
            "What-if Simulator",
            "Match Schedule",
        ]
    )

    with tab1:
        render_trophy_predictions(trophy, master, upsets)
        render_footer()

    with tab2:
        render_team_deep_dive(data)
        render_footer()

    with tab3:
        render_giant_killings(upsets)
        render_footer()

    with tab4:
        render_what_if(data)
        render_footer()

    with tab5:
        render_match_schedule()
        render_footer()


if __name__ == "__main__":
    main()
