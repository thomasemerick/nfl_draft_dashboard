import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import nflreadpy as nfl
import re

st.set_page_config(page_title="2026 NFL OL Stability", page_icon="🏈", layout="wide")

# ── Data loading ──
@st.cache_data
def load_data():
    import re

    def clean_name(name):
        if pd.isna(name): return name
        return re.sub(r'\s+(Jr\.|Sr\.|II|III|IV)$', '', str(name).strip()).strip()

    team_map_snap    = {"KAN":"KC","SFO":"SF","TAM":"TB","GNB":"GB","NWE":"NE","NOR":"NO","LAR":"LA","LVR":"LV"}
    team_map_roster  = {"KAN":"KC","SFO":"SF","TAM":"TB","GNB":"GB","NWE":"NE","NOR":"NO","LAR":"LA","LVR":"LV"}

    # 2026 projected starters
    depth = nfl.load_depth_charts().to_pandas()
    ol_positions = ["LT","LG","C","RG","RT"]
    starters = depth[
        (depth["pos_abb"].isin(ol_positions)) &
        (depth["pos_rank"] == 1)
    ].copy()
    starters = starters.sort_values("dt", ascending=False)
    starters = starters.drop_duplicates(subset=["team","pos_abb"], keep="first")
    starters = starters[["team","player_name","gsis_id","pos_abb"]].copy()
    starters["player_clean"] = starters["player_name"].apply(clean_name)

    # 2025 snap counts
    snaps_url = "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2025.csv"
    snaps = pd.read_csv(snaps_url)

    week1 = snaps[
        (snaps["week"] == 1) &
        (snaps["position"].isin(["T","G","C","OL"]))
    ][["player","team","offense_pct"]].copy()
    week1["week1_starter"] = week1["offense_pct"] >= 0.5

    season = snaps[
        snaps["position"].isin(["T","G","C","OL"])
    ].groupby(["player","team"]).agg(avg_offense_pct=("offense_pct","mean")).reset_index()
    season["season_incumbent"] = season["avg_offense_pct"] >= 0.5

    snap_summary = season.merge(week1[["player","team","week1_starter"]], on=["player","team"], how="left")
    snap_summary["week1_starter"] = snap_summary["week1_starter"].fillna(False)
    snap_summary["incumbent_2025"] = snap_summary["week1_starter"] | snap_summary["season_incumbent"]
    snap_summary["team"] = snap_summary["team"].replace(team_map_snap)
    snap_summary["player_clean"] = snap_summary["player"].apply(clean_name)

    # 2025 rosters
    rosters_2025 = nfl.load_rosters(seasons=[2025]).to_pandas()
    rosters_2025["full_name_clean"] = rosters_2025["full_name"].apply(clean_name)
    rosters_2025["team"] = rosters_2025["team"].replace(team_map_roster)
    roster_status = rosters_2025.groupby(["full_name_clean","team"])["status"].apply(
        lambda x: "RES" if "RES" in x.values else x.iloc[0]
    ).reset_index()

    # 2026 rookies
    draft_2026 = pd.read_excel("NFL-Draft-Book-2026.xlsx")
    draft_2026.columns = ["selection","round","pick","team","player","pos","age",
                          "college","pick_value","consensus","consensus_value","value_diff"]
    draft_2026["player_clean"] = draft_2026["player"].apply(clean_name)
    rookies_2026 = set(draft_2026["player_clean"].tolist())

    # Merge
    merged = starters.merge(
        snap_summary[["player_clean","team","incumbent_2025","avg_offense_pct","week1_starter"]],
        on=["player_clean","team"], how="left"
    )
    merged["incumbent_2025"] = merged["incumbent_2025"].fillna(False)

    def get_designation(row):
        name = row["player_clean"]
        team = row["team"]
        if row["incumbent_2025"]: return "Incumbent"
        if name in rookies_2026: return "Rookie"
        match = roster_status[
            (roster_status["full_name_clean"] == name) &
            (roster_status["team"] == team)
        ]
        if len(match) > 0:
            return "IR Return" if match.iloc[0]["status"] == "RES" else "New"
        return "New"

    merged["designation"] = merged.apply(get_designation, axis=1)

    # Team summary
    team_summary = merged.groupby("team")["designation"].value_counts().unstack(fill_value=0).reset_index()
    for col in ["Incumbent","New","Rookie","IR Return"]:
        if col not in team_summary.columns:
            team_summary[col] = 0
    team_summary["incumbents"] = team_summary["Incumbent"]
    team_summary = team_summary.sort_values("incumbents", ascending=False)

    return merged, team_summary

merged, team_summary = load_data()

# ── Header ──
st.title("🏈 2026 NFL Offensive Line Stability")
st.markdown("*Projected 2026 starting OL — Incumbent = started Week 1 or 50%+ offensive snaps in 2025 for same team*")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Team Stability", "🔵 OL Visualizer", "🏆 League Overview"])

# ════════════════════════════════
# TAB 1 — Team Stability Table
# ════════════════════════════════
with tab1:
    st.subheader("OL Returning Starter Count by Team")

    # Build bucket columns 0-5
    display = team_summary[["team","incumbents","Incumbent","New","Rookie","IR Return"]].copy()
    display.columns = ["Team","Incumbents","Incumbent","New","Rookie","IR Return"]

    # Add bucket column
    display["Returning Starters"] = display["Incumbents"].astype(str) + " / 5"

    # Sort by incumbents desc
    display = display.sort_values("Incumbents", ascending=False).reset_index(drop=True)

    # Color code the Incumbents column
    def color_incumbents(val):
        if val == 5:   return "background-color: #1D9E75; color: white"
        if val == 4:   return "background-color: #90D4B5; color: black"
        if val == 3:   return "background-color: #FFF3CD; color: black"
        if val == 2:   return "background-color: #FFD580; color: black"
        if val <= 1:   return "background-color: #FF9999; color: black"
        return ""

    styled = display[["Team","Returning Starters","Incumbent","New","Rookie","IR Return"]].style.map(
        color_incumbents, subset=["Incumbent"]
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.markdown("""
**Incumbent** — started Week 1 2025 or took 50%+ offensive snaps in 2025 for same team  
**New** — signed via free agency or trade  
**Rookie** — 2026 draft pick  
**IR Return** — on 2025 roster but missed season due to injury  
*Snap count threshold: one standard deviation from mean offensive snap percentage among OL*
""")

# ════════════════════════════════
# TAB 2 — OL Visualizer
# ════════════════════════════════
with tab2:
    st.subheader("Team OL Lineup Visualizer")
    selected_team = st.selectbox("Select Team", sorted(merged["team"].unique()))

    team_ol = merged[merged["team"] == selected_team].copy()

    # Position order left to right
    pos_order = ["LT","LG","C","RG","RT"]
    pos_labels = {"LT":"Left Tackle","LG":"Left Guard","C":"Center","RG":"Right Guard","RT":"Right Tackle"}
    team_ol["pos_order"] = team_ol["pos_abb"].map({p:i for i,p in enumerate(pos_order)})
    team_ol = team_ol.sort_values("pos_order")

    fig = go.Figure()

    for _, row in team_ol.iterrows():
        is_incumbent = row["designation"] == "Incumbent"
        is_rookie = row["designation"] == "Rookie"
        color = "#378ADD" if is_incumbent else "#FFD580"
        text_color = "white" if is_incumbent else "black"
        x_pos = pos_order.index(row["pos_abb"])

        # Main box
        fig.add_shape(
            type="rect",
            x0=x_pos - 0.45, x1=x_pos + 0.45,
            y0=0.25, y1=0.95,
            fillcolor=color,
            line=dict(color="white", width=2)
        )

        # Player name
        fig.add_annotation(
            x=x_pos, y=0.68,
            text=f"<b>{row['player_name']}</b>",
            showarrow=False,
            font=dict(size=20, color=text_color),
            align="center"
        )

        # Position label
        fig.add_annotation(
            x=x_pos, y=0.42,
            text=pos_labels[row["pos_abb"]],
            showarrow=False,
            font=dict(size=15, color=text_color),
            align="center"
        )

        # Rookie tag underneath
        if is_rookie:
            fig.add_shape(
                type="rect",
                x0=x_pos - 0.45, x1=x_pos + 0.45,
                y0=0.08, y1=0.22,
                fillcolor="#2ECC71",
                line=dict(color="white", width=2)
            )
            fig.add_annotation(
                x=x_pos, y=0.15,
                text="<b>ROOKIE</b>",
                showarrow=False,
                font=dict(size=13, color="white"),
                align="center"
            )

    fig.update_layout(
        height=320,
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[-0.6, 4.6]),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[0, 1]),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        title=f"{selected_team} — 2026 Projected Starting OL"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Simple legend
    col1, col2 = st.columns(2)
    col1.markdown("🔵 **Incumbent** — took more than 50% snaps or started Week 1 on same team in 2025")
    col2.markdown("🟡 **Non-Incumbent** — does not meet threshold for incumbent status")

# ════════════════════════════════
# TAB 3 — League Overview
# ════════════════════════════════
with tab3:
    st.subheader("League-Wide OL Stability Overview")

    col1, col2 = st.columns(2)

    with col1:
        # Distribution of incumbent counts
        bucket_counts = team_summary["incumbents"].value_counts().sort_index().reset_index()
        bucket_counts.columns = ["Returning Starters","Teams"]
        fig_dist = px.bar(
            bucket_counts,
            x="Returning Starters", y="Teams",
            color="Returning Starters",
            color_continuous_scale=["#FF9999","#FFD580","#FFF3CD","#90D4B5","#1D9E75","#0D6B4F"],
            title="How Many Teams Have X Returning OL Starters",
            labels={"Returning Starters":"# Returning Starters","Teams":"# of Teams"}
        )
        fig_dist.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_dist, use_container_width=True)

    with col2:
        # Designation breakdown league-wide
        des_counts = merged["designation"].value_counts().reset_index()
        des_counts.columns = ["Designation","Count"]
        color_map = {"Incumbent":"#378ADD","New":"#FFD580","Rookie":"#FFD580","IR Return":"#FFD580"}
        fig_pie = px.pie(
            des_counts, values="Count", names="Designation",
            title="League-Wide OL Starter Breakdown",
            color="Designation",
            color_discrete_map=color_map
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # Rookie starters by team
    st.subheader("Teams Starting Rookies on OL")
    rookies = merged[merged["designation"] == "Rookie"][["team","player_name","pos_abb"]].sort_values("team")
    if len(rookies) > 0:
        st.dataframe(rookies.rename(columns={"team":"Team","player_name":"Player","pos_abb":"Position"}).reset_index(drop=True),
                     use_container_width=True, hide_index=True)
    else:
        st.write("No rookie starters found.")

    st.divider()

   # Incumbent bucket table
    st.subheader("Starting OL Continuity: Total Incumbents")
    st.caption("Incumbents = took more than 50% snaps or started Week 1 on same team last year.")

    # Build bucket columns 1-5
    buckets = {i: [] for i in range(6)}
    for _, row in team_summary.iterrows():
        buckets[row["incumbents"]].append(row["team"])

    max_len = max(len(v) for v in buckets.values())
    bucket_df = pd.DataFrame({
        str(i): buckets[i] + [""] * (max_len - len(buckets[i]))
        for i in range(6)
    })

    # Drop column 0 if empty
    bucket_df = bucket_df[[c for c in bucket_df.columns if c != "0" or any(bucket_df["0"] != "")]]

    def color_bucket(val):
        if val == "": return ""
        col = val.name if hasattr(val, 'name') else ""
        colors = {"1":"#CC3333","2":"#CC3333","3":"#FFD580","4":"#90D4B5","5":"#1D9E75"}
        return ""

    # Style header colors
    col_colors = {"1":"#CC3333","2":"#e07b7b","3":"#FFD580","4":"#90D4B5","5":"#1D9E75"}

    styled_bucket = bucket_df.style.apply(
        lambda col: [
            f"background-color: {col_colors.get(col.name, 'white')}; color: white; font-weight: bold; text-align: center"
            if v != "" else ""
            for v in col
        ], axis=0
    ).set_table_styles([
        {"selector": f"th.col_heading.col{i}",
         "props": [("background-color", list(col_colors.values())[i]), ("color", "white"), ("font-weight", "bold"), ("text-align", "center")]}
        for i in range(len(col_colors))
    ])

    st.dataframe(styled_bucket, use_container_width=True, hide_index=True)