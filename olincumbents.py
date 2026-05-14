import nflreadpy as nfl
import pandas as pd

# Load current depth charts
depth = nfl.load_depth_charts().to_pandas()

# Filter to OL positions and starters only
ol_positions = ["LT", "LG", "C", "RG", "RT"]

starters_2026 = depth[
    (depth["pos_abb"].isin(ol_positions)) &
    (depth["pos_rank"] == 1)
].copy()

# Keep only the most recent entry per team/position
starters_2026 = starters_2026.sort_values("dt", ascending=False)
starters_2026 = starters_2026.drop_duplicates(subset=["team","pos_abb"], keep="first")

starters_2026 = starters_2026[["team","player_name","gsis_id","pos_abb"]].copy()

print(f"Total projected OL starters: {len(starters_2026)}")
print(starters_2026.sort_values(["team","pos_abb"]).to_string(index=False))

# Load 2025 snap counts
snaps_url = "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2025.csv"
snaps = pd.read_csv(snaps_url)
print(snaps.columns.tolist())
print(snaps.shape)
print(snaps.head(3))

# Check name format and Week 1 starters
print(snaps[snaps["week"] == 1][["player","pfr_player_id","team","position","offense_pct"]].head(10))

# Also check what OL positions look like
ol_snaps = snaps[snaps["position"].isin(["T","G","C","OL"])]
print(ol_snaps["position"].value_counts())

# Aggregate 2025 snap counts per player
# Week 1 starter = offense_pct >= 0.5 in week 1
# Full season incumbent = avg offense_pct >= 0.5 across season

week1_snaps = snaps[
    (snaps["week"] == 1) &
    (snaps["position"].isin(["T","G","C","OL"]))
][["player","team","offense_pct"]].copy()
week1_snaps["week1_starter"] = week1_snaps["offense_pct"] >= 0.5

season_snaps = snaps[
    snaps["position"].isin(["T","G","C","OL"])
].groupby(["player","team"]).agg(
    avg_offense_pct=("offense_pct","mean")
).reset_index()
season_snaps["season_incumbent"] = season_snaps["avg_offense_pct"] >= 0.5

# Merge both into one snap summary
snap_summary = season_snaps.merge(
    week1_snaps[["player","team","week1_starter"]],
    on=["player","team"],
    how="left"
)
snap_summary["week1_starter"] = snap_summary["week1_starter"].fillna(False)
snap_summary["incumbent_2025"] = snap_summary["week1_starter"] | snap_summary["season_incumbent"]

print(snap_summary.head(10).to_string(index=False))

# Convert snap data team codes to match depth chart codes
team_map = {"KAN": "KC", "SFO": "SF", "TAM": "TB", "GNB": "GB", 
            "NWE": "NE", "NOR": "NO", "LAR": "LA", "LVR": "LV"}
snap_summary["team"] = snap_summary["team"].replace(team_map)

print(snap_summary[snap_summary["player"].isin(["Creed Humphrey","Trey Smith","Trent Williams","Tristan Wirfs"])][["player","team"]])

# Merge 2026 starters against 2025 snap incumbents on name + team
merged = starters_2026.merge(
    snap_summary[["player","team","incumbent_2025","avg_offense_pct","week1_starter"]],
    left_on=["player_name","team"],
    right_on=["player","team"],
    how="left"
)

merged["incumbent_2025"] = merged["incumbent_2025"].fillna(False)

# Count incumbents per team
incumbent_count = merged.groupby("team").agg(
    incumbents=("incumbent_2025","sum"),
    total=("player_name","count")
).reset_index()

incumbent_count["incumbents"] = incumbent_count["incumbents"].astype(int)
incumbent_count = incumbent_count.sort_values("incumbents", ascending=False)

print("\nOL Incumbent Count by Team (2026 Projected Starters who started in 2025):")
print(incumbent_count.to_string(index=False))

# Show detail for any team with 0 incumbents
print("\nNon-incumbent projected starters:")
print(merged[merged["incumbent_2025"] == False][
    ["team","player_name","pos_abb","avg_offense_pct"]
].sort_values(["team","pos_abb"]).to_string(index=False))

import re

def clean_name(name):
    if pd.isna(name):
        return name
    # Remove suffixes
    name = re.sub(r'\s+(Jr\.|Sr\.|II|III|IV)$', '', str(name).strip())
    return name.strip()

starters_2026["player_clean"] = starters_2026["player_name"].apply(clean_name)
snap_summary["player_clean"] = snap_summary["player"].apply(clean_name)

# Merge on cleaned name + team
merged = starters_2026.merge(
    snap_summary[["player_clean","team","incumbent_2025","avg_offense_pct","week1_starter"]],
    left_on=["player_clean","team"],
    right_on=["player_clean","team"],
    how="left"
)

merged["incumbent_2025"] = merged["incumbent_2025"].fillna(False)

incumbent_count = merged.groupby("team").agg(
    incumbents=("incumbent_2025","sum"),
    total=("player_name","count")
).reset_index()

incumbent_count["incumbents"] = incumbent_count["incumbents"].astype(int)
incumbent_count = incumbent_count.sort_values("incumbents", ascending=False)

print("\nOL Incumbent Count by Team:")
print(incumbent_count.to_string(index=False))

# Load 2025 rosters to identify IR returns vs new additions
rosters_2025 = nfl.load_rosters(seasons=[2025]).to_pandas()
print(rosters_2025.columns.tolist())
print(rosters_2025["status"].value_counts())

# Normalize roster names and teams
rosters_2025["full_name_clean"] = rosters_2025["full_name"].apply(clean_name)
team_map_roster = {"KAN": "KC", "SFO": "SF", "TAM": "TB", "GNB": "GB",
                   "NWE": "NE", "NOR": "NO", "LAR": "LA", "LVR": "LV"}
rosters_2025["team"] = rosters_2025["team"].replace(team_map_roster)

# Get 2025 roster status per player per team
roster_status = rosters_2025.groupby(["full_name_clean","team"])["status"].apply(
    lambda x: "RES" if "RES" in x.values else x.iloc[0]
).reset_index()

# Get 2026 rookies from your draft data
draft_2026 = pd.read_excel("NFL-Draft-Book-2026.xlsx")
draft_2026.columns = ["selection","round","pick","team","player","pos","age",
                       "college","pick_value","consensus","consensus_value","value_diff"]
draft_2026["player_clean"] = draft_2026["player"].apply(clean_name)
rookies_2026 = set(draft_2026["player_clean"].tolist())

# Build final designation
def get_designation(row):
    name = row["player_clean"]
    team = row["team"]

    # Check if incumbent
    if row["incumbent_2025"]:
        return "Incumbent"

    # Check if rookie
    if name in rookies_2026:
        return "Rookie"

    # Check 2025 roster status
    match = roster_status[
        (roster_status["full_name_clean"] == name) &
        (roster_status["team"] == team)
    ]
    if len(match) > 0:
        status = match.iloc[0]["status"]
        if status == "RES":
            return "IR Return"
        else:
            return "New"

    # Not found on same team's roster at all
    return "New"

merged["designation"] = merged.apply(get_designation, axis=1)

# Summary by team
print("\nFull OL Designation by Team:")
for team in sorted(merged["team"].unique()):
    team_df = merged[merged["team"] == team][["player_name","pos_abb","designation"]]
    incumbents = len(team_df[team_df["designation"] == "Incumbent"])
    print(f"\n{team} — {incumbents}/5 Incumbents")
    print(team_df.to_string(index=False))

    # Clean summary table
summary = merged[["team","pos_abb","player_name","designation"]].sort_values(["team","pos_abb"])

# Team-level count
team_summary = merged.groupby("team")["designation"].value_counts().unstack(fill_value=0).reset_index()
print("\nTeam OL Stability Summary:")
print(team_summary.sort_values("Incumbent", ascending=False).to_string(index=False))

# Save to CSV
summary.to_csv("ol_incumbents_2026.csv", index=False)
print("\nSaved to ol_incumbents_2026.csv")