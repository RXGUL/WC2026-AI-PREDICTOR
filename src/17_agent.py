from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import os
import sys
import time
from typing import Any, TypedDict


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

from constants import ALL_TEAMS


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


news_fetcher = load_module("news_fetcher", SRC_DIR / "16_news_fetcher.py")


MASTER_TEAMS_PATH = PROJECT_ROOT / "data" / "processed" / "master_teams.csv"
TROPHY_PROBABILITIES_PATH = PROJECT_ROOT / "data" / "processed" / "trophy_probabilities.csv"
UPDATE_LOG_PATH = PROJECT_ROOT / "data" / "injuries" / "update_log.json"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"

PRODUCTION_SCAN_INTERVAL = 21_600
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL_SECONDS", str(PRODUCTION_SCAN_INTERVAL)))
MAX_CYCLES = int(os.getenv("AGENT_MAX_CYCLES", "0") or "0")


class AgentState(TypedDict):
    last_scan_time: datetime | None
    player_statuses: list[dict[str, Any]]
    changes_detected: list[dict[str, Any]]
    re_run_triggered: bool
    cycle_count: int
    log_messages: list[str]


def initial_state() -> AgentState:
    return {
        "last_scan_time": None,
        "player_statuses": [],
        "changes_detected": [],
        "re_run_triggered": False,
        "cycle_count": 0,
        "log_messages": [],
    }


def log(state: AgentState, message: str) -> AgentState:
    state["log_messages"].append(message)
    print(message)
    return state


def team_watchlist_key(team: str) -> str:
    return getattr(news_fetcher, "WATCHLIST_TEAM_ALIASES", {}).get(team, team)


def key_players_by_team() -> dict[str, set[str]]:
    watchlist = getattr(news_fetcher, "PLAYER_WATCHLIST", {})
    return {team: set(players[:3]) for team, players in watchlist.items()}


def monitor_node(state: AgentState) -> AgentState:
    previous_statuses = news_fetcher.load_previous_statuses()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    statuses = news_fetcher.run_news_scan()
    statuses_frame = news_fetcher.save_statuses(statuses, timestamp)
    changes = news_fetcher.detect_changes(statuses_frame, previous_statuses)
    news_fetcher.append_change_log(changes, timestamp)

    state["last_scan_time"] = datetime.now(timezone.utc)
    state["player_statuses"] = statuses
    state["changes_detected"] = changes
    state = log(state, f"Scan complete: {len(statuses)} players checked, {len(changes)} changes")
    return state


def decide_node(state: AgentState) -> AgentState:
    key_lookup = key_players_by_team()
    trigger_changes = []

    for change in state["changes_detected"]:
        team = str(change.get("team", ""))
        player = str(change.get("player", ""))
        confidence = str(change.get("confidence", "low")).lower()
        is_key = player in key_lookup.get(team, set())
        if is_key and confidence in {"medium", "high"}:
            trigger_changes.append(change)

    if trigger_changes:
        state["re_run_triggered"] = True
        names = ", ".join(
            f"{change['player']} ({change['team']}, {change['confidence']})"
            for change in trigger_changes
        )
        state = log(state, f"Decision: re-run triggered because key player status changed: {names}")
    else:
        state["re_run_triggered"] = False
        if state["changes_detected"]:
            state = log(state, "Decision: no re-run; changes did not involve key players at medium/high confidence")
        else:
            state = log(state, "Decision: no re-run; no status changes detected")

    return state


def update_master_injury_counts(statuses: list[dict[str, Any]], changed_teams: set[str]) -> list[str]:
    messages = []
    if not MASTER_TEAMS_PATH.exists():
        return [f"Skipped master_teams update; missing file: {MASTER_TEAMS_PATH}"]

    master = pd.read_csv(MASTER_TEAMS_PATH)
    if "team" not in master.columns:
        return [f"Skipped master_teams update; team column missing in {MASTER_TEAMS_PATH}"]

    if "injured_count" not in master.columns:
        master["injured_count"] = 0
    if "availability_score" not in master.columns:
        master["availability_score"] = 1.0

    statuses_by_team: dict[str, list[dict[str, Any]]] = {}
    for status in statuses:
        statuses_by_team.setdefault(str(status.get("team", "")), []).append(status)

    for team in sorted(changed_teams):
        team_statuses = statuses_by_team.get(team, [])
        if not team_statuses:
            continue

        unavailable_count = sum(
            str(row.get("status", "")).lower() in {"injured", "doubt"}
            for row in team_statuses
        )
        availability = max(0.0, 1.0 - (unavailable_count / max(len(team_statuses), 1)))

        mask = master["team"].astype(str).eq(team)
        if not mask.any():
            messages.append(f"Team {team} not found in master_teams.csv; injury count not updated")
            continue

        master.loc[mask, "injured_count"] = unavailable_count
        master.loc[mask, "availability_score"] = round(availability, 3)
        messages.append(f"Updated {team}: injured_count={unavailable_count}, availability_score={availability:.3f}")

    master.to_csv(MASTER_TEAMS_PATH, index=False)
    return messages


def run_monte_carlo(state: AgentState) -> None:
    monte_carlo = load_module("monte_carlo", SRC_DIR / "14_monte_carlo.py")
    monte_carlo.main()


def trophy_leader() -> tuple[str, float]:
    if not TROPHY_PROBABILITIES_PATH.exists():
        return "unknown", 0.0
    trophy = pd.read_csv(TROPHY_PROBABILITIES_PATH)
    if trophy.empty or "team" not in trophy.columns or "trophy_probability" not in trophy.columns:
        return "unknown", 0.0
    leader = trophy.sort_values("trophy_probability", ascending=False).iloc[0]
    return str(leader["team"]), float(leader["trophy_probability"])


def regenerate_reports_for_teams(teams: set[str], state: AgentState) -> None:
    if not teams:
        return

    report_module = load_module("generate_reports", SRC_DIR / "15_generate_reports.py")
    report_module.load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        state = log(state, "Skipped report regeneration; OPENAI_API_KEY missing")
        return

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    dataframes = report_module.load_dataframes()
    contexts = report_module.build_contexts(dataframes)
    context_lookup = {context["team"]: context for context in contexts}
    client = report_module.OpenAI(api_key=api_key)

    all_reports_path = REPORTS_DIR / "all_reports.json"
    if all_reports_path.exists():
        reports = json.loads(all_reports_path.read_text(encoding="utf-8"))
    else:
        reports = {}

    for team in sorted(teams):
        context = context_lookup.get(team)
        if not context:
            state = log(state, f"Skipped report regeneration for {team}; context missing")
            continue
        try:
            report = report_module.generate_report(client, context)
        except Exception as exc:
            state = log(state, f"Report regeneration failed for {team}: {exc}")
            report = "Report unavailable"
        report_module.save_report(team, report)
        reports[team] = report
        time.sleep(0.5)

    all_reports_path.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")


def update_node(state: AgentState) -> AgentState:
    changed_teams = {str(change.get("team")) for change in state["changes_detected"] if change.get("team")}

    for message in update_master_injury_counts(state["player_statuses"], changed_teams):
        state = log(state, message)

    try:
        run_monte_carlo(state)
    except Exception as exc:
        state = log(state, f"Monte Carlo re-run failed: {exc}")

    try:
        regenerate_reports_for_teams(changed_teams, state)
    except Exception as exc:
        state = log(state, f"Changed-team report regeneration failed: {exc}")

    leader_team, leader_pct = trophy_leader()
    state = log(state, f"Re-run complete. New trophy leader: {leader_team} {leader_pct:.2f}%")

    UPDATE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "changed_teams": sorted(changed_teams),
        "changes_detected": state["changes_detected"],
        "re_run_triggered": state["re_run_triggered"],
        "new_trophy_leader": {"team": leader_team, "trophy_probability": leader_pct},
        "log_messages": state["log_messages"],
    }
    UPDATE_LOG_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return state


def wait_node(state: AgentState) -> AgentState:
    print("Next scan in 6 hours... (Ctrl+C to stop)")
    time.sleep(SCAN_INTERVAL)
    state["cycle_count"] += 1
    return state


def should_update(state: AgentState) -> str:
    return "update_node" if state["re_run_triggered"] else "wait_node"


def should_continue(state: AgentState) -> str:
    if MAX_CYCLES and state["cycle_count"] >= MAX_CYCLES:
        return "end"
    return "monitor_node"


def print_graph_structure(langgraph_available: bool) -> None:
    engine = "LangGraph" if langgraph_available else "fallback loop"
    print(f"\nAgent graph structure ({engine})")
    print("-" * 72)
    print("START -> monitor_node")
    print("monitor_node -> decide_node")
    print("decide_node -> update_node [if re_run_triggered=True]")
    print("decide_node -> wait_node [if re_run_triggered=False]")
    print("update_node -> wait_node")
    print("wait_node -> monitor_node")


def build_langgraph():
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        print("pip install langgraph langchain langchain-openai")
        return None

    graph = StateGraph(AgentState)
    graph.add_node("monitor_node", monitor_node)
    graph.add_node("decide_node", decide_node)
    graph.add_node("update_node", update_node)
    graph.add_node("wait_node", wait_node)

    graph.add_edge(START, "monitor_node")
    graph.add_edge("monitor_node", "decide_node")
    graph.add_conditional_edges(
        "decide_node",
        should_update,
        {"update_node": "update_node", "wait_node": "wait_node"},
    )
    graph.add_edge("update_node", "wait_node")
    graph.add_conditional_edges(
        "wait_node",
        should_continue,
        {"monitor_node": "monitor_node", "end": END},
    )
    return graph.compile()


def run_fallback_loop(state: AgentState) -> AgentState:
    while True:
        state = monitor_node(state)
        state = decide_node(state)
        if state["re_run_triggered"]:
            state = update_node(state)
        state = wait_node(state)
        if MAX_CYCLES and state["cycle_count"] >= MAX_CYCLES:
            return state


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    compiled_graph = build_langgraph()
    print_graph_structure(compiled_graph is not None)
    state = initial_state()

    if compiled_graph is not None:
        compiled_graph.invoke(state, config={"recursion_limit": 1_000})
    else:
        run_fallback_loop(state)


if __name__ == "__main__":
    main()
