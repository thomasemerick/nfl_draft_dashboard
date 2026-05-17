import pandas as pd
import re

def clean_name(name):
    if pd.isna(name): return name
    return re.sub(r'\s+(Jr\.|Sr\.|II|III|IV)$', '', str(name).strip()).strip()

nickname_map = {
    "Delmar Glaze": "DJ Glaze",
    "Michael Onwenu": "Mike Onwenu",
    "Olu Fashanu": "Olumuyiwa Fashanu",
}

def normalize_name(name):
    name = clean_name(name)
    return nickname_map.get(name, name)

team_map = {"KAN":"KC","SFO":"SF","TAM":"TB","GNB":"GB","NWE":"NE",
            "NOR":"NO","LAR":"LA","LVR":"LV","OAK":"LV","STL":"LA","SDG":"LAC"}

ol_positions = ["LT","LG","C","RG","RT"]
seasons = list(range(2020, 2026))

# Load all snap counts 2019-2025
print("Loading snap counts...")
snaps_all = []
for year in range(2019, 2026):
    url = f"https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{year}.csv"
    df = pd.read_csv(url)
    snaps_all.append(df)
snaps_hist = pd.concat(snaps_all, ignore_index=True)
snaps_hist = snaps_hist[snaps_hist["week"] <= 18]
snaps_hist["player_clean"] = snaps_hist["player"].apply(normalize_name)
snaps_hist["team"] = snaps_hist["team"].replace(team_map)
print(f"Snap data loaded: {snaps_hist['season'].value_counts().sort_index().to_dict()}")

# Load depth charts
print("Loading depth charts...")
import nflreadpy as nfl
depth_all = nfl.load_depth_charts(seasons=seasons).to_pandas()
depth_all["team"] = depth_all["team"].replace(team_map)
depth_all["player_clean"] = depth_all["player_name"].apply(normalize_name)
print(f"Depth chart seasons: {sorted(depth_all['season'].unique())}")
print(depth_all.columns.tolist())
print(depth_all[depth_all["season"] == 2024.0][["season","team","player_name","pos_abb","pos_rank"]].head(10).to_string(index=False))


# Load PFR-based continuity scores
continuity_df = pd.read_csv("pfr_week1_continuity.csv")
print(continuity_df["season"].value_counts().sort_index())

# Load play by play for total yards
print("Loading play by play data for total yards...")
yards_all = []
for year in range(2020, 2026):
    url = f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{year}.csv"
    pbp = pd.read_csv(url, low_memory=False, usecols=["season","week","posteam","yards_gained"])
    pbp = pbp[(pbp["week"] <= 18) & (pbp["posteam"].notna())]
    team_yards = pbp.groupby("posteam")["yards_gained"].sum().reset_index()
    team_yards.columns = ["team","total_yards"]
    team_yards["season"] = year
    yards_all.append(team_yards)
    print(f"  {year}: loaded")

yards_df = pd.concat(yards_all, ignore_index=True)
pbp_team_map = {"LA": "LAR", "LV": "LV"}
yards_df["team"] = yards_df["team"].replace(pbp_team_map)

# Merge with continuity
final_df = continuity_df.merge(yards_df, on=["team","season"], how="left")
final_df["total_yards"] = final_df["total_yards"].fillna(0).round(0).astype(int)
final_df["yards_rank"] = final_df.groupby("season")["total_yards"].rank(ascending=False).astype(int)

print(final_df.sort_values(["season","team"]).head(20).to_string(index=False))
final_df.to_csv("ol_historical.csv", index=False)
print(f"\nSaved to ol_historical.csv — {len(final_df)} rows")