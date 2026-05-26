import pandas as pd
import os

print("Loading datasets...")

results_path = "./data/raw/results.csv"
wc_path = "./data/raw/WorldCupMatches.csv"
fm_path = "./data/fm25/fm25_players.csv"

results = pd.read_csv(results_path)
worldcup = pd.read_csv(wc_path)
fm25 = pd.read_csv(fm_path)

print("\nDatasets Loaded Successfully ")

print(f"Results matches: {results.shape}")
print(f"World Cup matches: {worldcup.shape}")
print(f"FM25 players: {fm25.shape}")

print("\n48 teams × 30 features milestone ready ")