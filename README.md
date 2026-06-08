# WC2026 AI Predictor

An end-to-end machine learning system built to predict the 2026 FIFA World Cup — 
built in 16 days, live before the opening match.

🔗 [Live Dashboard] (https://wc2026-ai-predictor.streamlit.app)

---

## What It Does

- Predicts trophy probability for all 48 WC2026 teams
- Runs 10,000 Monte Carlo tournament simulations per update
- Tracks 165 player fitness statuses via an autonomous LangGraph agent
- Flags giant-killing upset risks across all group stage matchups
- Generates GPT-4o analyst reports for every team
- Updates predictions in real time as player news breaks

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| ML Model | XGBoost |
| Simulations | Monte Carlo (10,000 runs) |
| Agentic Pipeline | LangGraph + GPT-4o |
| Data Sources | football-data.org, Google News RSS, ELO ratings |
| Backend | Supabase (live database) |
| Frontend | Streamlit |
| Deployment | Streamlit Cloud |

---

## Features Engineered (59 total)

- ELO rating & ELO differential
- Squad market value
- Recent form index
- Head-to-head record
- Home advantage
- Confederation strength
- FIFA rank
- Composure & mentality score
- Climate fatigue index
- Google News sentiment score
- Disciplinary risk profile
- Tactical formation tendencies

---

## Dashboard Tabs

| Trophy Predictions | Full probability rankings, Monte Carlo confidence, leaderboard |
| Team Deep Dive | ELO, squad value, pressure index, player status, GPT-4o report |
| Giant Killings | Upset probability radar across all matchups |
| What-If Simulator | Adjust team conditions, re-run 10,000 simulations live |
| Match Schedule | All 104 matches with stage filtering and live updates |

---

## Build Timeline

| Days | What Was Built |
|------|---------------|
| 1–2 | Data pipeline, ELO ratings, form index, H2H features |
| 3 | XGBoost trained, SHAP explainability, giant killer model |
| 4 | GPT-4o analyst reports for all 48 teams |
| 5 | LangGraph news agent — 165 player statuses tracked |
| 6 | Streamlit dashboard live — Trophy, Deep Dive, Giant Killings, What-If |
| 7 | Monte Carlo simulations — 10,000 runs per update |
| 8–9 | Supabase live backend, climate fatigue, venue features |
| 10 | Sentiment scoring + disciplinary risk — model retrained |
| 11–12 | Full dashboard UI overhaul, match schedule tab, mobile fixes |
| 13 | Final pre-tournament agent rescan — rankings confirmed |

---

## Results (Pre-Tournament)

| Rank | Team | Trophy % | Final % |
|------|------|----------|---------|
| 1 | Spain | 15.36% | 24.12% |
| 2 | Argentina | 11.03% | 19.16% |
| 3 | Brazil | 10.25% | 17.28% |
| 4 | France | 8.09% | 13.48% |
| 5 | England | 6.78% | 13.09% |

**Biggest upset risk:** DR Congo over Colombia — 36.2%

---

## Author

Built by Ragul Velmurugan  
[LinkedIn](https://linkedin.com/in/ragulvelmurugan) · 
[GitHub](https://github.com/RXGUL)

---

## Project Structure
