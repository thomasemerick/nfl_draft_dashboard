import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import nflreadpy as nfl
import re

st.set_page_config(page_title="2026 NFL OL Continuity", page_icon="🏈", layout="wide")
st.markdown("""
    <style>
    [data-testid="stSidebarNavItems"] li:first-child {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)
# ── Data loading ──
@st.cache_data
def load_data():
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
    starters["player_clean"] = starters["player_name"].apply(normalize_name)

    # 2025 snap counts
    snaps_url = "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2025.csv"
    snaps = pd.read_csv(snaps_url)

    week1 = snaps[
        (snaps["week"] == 1) &
        (snaps["game_type"] == "REG") &
        (snaps["position"].isin(["T","G","C","OL"]))
    ][["player","team","offense_pct"]].copy()
    week1["week1_starter"] = week1["offense_pct"] >= 0.5

    ol_snaps_raw = snaps[(snaps["position"].isin(["T","G","C","OL"])) & (snaps["game_type"] == "REG")].copy()
    player_totals = ol_snaps_raw.groupby(["player","team"]).agg(total_snaps=("offense_snaps","sum")).reset_index()
    team_totals = snaps[snaps["game_type"]=="REG"].groupby(["team","game_id"]).agg(max_snaps=("offense_snaps","max")).reset_index().groupby("team")["max_snaps"].sum().reset_index()
    team_totals.columns = ["team","team_total_snaps"]
    season = player_totals.merge(team_totals, on="team", how="left")
    season["avg_offense_pct"] = season["total_snaps"] / season["team_total_snaps"]
    season["season_incumbent"] = season["avg_offense_pct"] >= 0.5

    snap_summary = season.merge(week1[["player","team","week1_starter"]], on=["player","team"], how="left")
    snap_summary["week1_starter"] = snap_summary["week1_starter"].fillna(False)
    snap_summary["incumbent_2025"] = snap_summary["week1_starter"] | snap_summary["season_incumbent"]
    snap_summary["team"] = snap_summary["team"].replace(team_map_snap)
    snap_summary["player_clean"] = snap_summary["player"].apply(normalize_name)

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
        if row["incumbent_2025"]: return "Returning Starter"
        if name in rookies_2026: return "Rookie"
        match = roster_status[
            (roster_status["full_name_clean"] == name) &
            (roster_status["team"] == team)
        ]

        if len(match) > 0:
            status = match.iloc[0]["status"]
            avg_pct = row.get("avg_offense_pct", 0)
            if pd.isna(avg_pct):
                avg_pct = 0
            if status == "RES" and avg_pct == 0:
                return "Missed Year"
            elif status == "RES" and avg_pct > 0:
                return "Full-time Jump"
            else:
                return "Full-time Jump"
        return "Free Agent / Trade"

    merged["designation"] = merged.apply(get_designation, axis=1)

    # Team summary
    team_summary = merged.groupby("team")["designation"].value_counts().unstack(fill_value=0).reset_index()
    for col in ["Returning Starter","Full-time Jump","Free Agent / Trade","Rookie","Missed Year"]:
        if col not in team_summary.columns:
            team_summary[col] = 0
    team_summary["incumbents"] = team_summary["Returning Starter"]
    team_summary["incumbents"] = team_summary["Returning Starter"]
    team_summary = team_summary.sort_values("incumbents", ascending=False)
    display_team_map = {"LA": "LAR"}
    merged["team"] = merged["team"].replace(display_team_map)
    team_summary["team"] = team_summary["team"].replace(display_team_map)
    return merged, team_summary

merged, team_summary = load_data()

# ── Header ──
st.title("🏈 NFL Offensive Line Continuity Explorer")
st.markdown("*Quantifying year-over-year continuity for projected starting units across the league*")
st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📊 League Overview", "🔵 Team Breakdown", "🏆 Continuity Viz", "📈 Historical"])

# ════════════════════════════════
# TAB 1 — OL Continuity Table
# ════════════════════════════════
with tab1:
    st.subheader("Starting Offensive Lines in 2026: Total Returning Starters by Team")

    # Build bucket columns 0-5
    display = team_summary[["team","incumbents","Returning Starter","Full-time Jump","Free Agent / Trade","Rookie","Missed Year"]].copy()
    display.columns = ["Team","Returning Starters","Returning Starter","Full-time Jump","Free Agent / Trade","Rookie","Missed Year"]

    # Add bucket column
    display["Returning Starters"] = display["Returning Starters"].astype(str) + " / 5"

    # Sort by Returning Starters desc
    display = display.sort_values("Returning Starters", ascending=False).reset_index(drop=True)

    # Color code the Returning Starters column
    def color_incumbents(val):
        try:
            n = int(str(val).split("/")[0].strip())
        except:
            return ""
        if n == 5:   return "background-color: #1D9E75; color: white"
        if n == 4:   return "background-color: #90D4B5; color: black"
        if n == 3:   return "background-color: #FFF3CD; color: black"
        if n == 2:   return "background-color: #FFD580; color: black"
        if n <= 1:   return "background-color: #FF9999; color: black"
        return ""

    styled = display[["Team","Returning Starters","Full-time Jump","Free Agent / Trade","Rookie","Missed Year"]].style.map(
    color_incumbents, subset=["Returning Starters"]
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.markdown("""
**Returning Starter** — started Week 1 2025 or took 50%+ offensive snaps in 2025 for same team  
**Full-time Jump** — on the same 2025 roster but did not meet returning starter threshold  
**Free Agent / Trade** — signed via free agency or trade (rookies excluded)   
**Rookie** — 2026 draft pick or 2026 rookie UDFA signing   
**Missed Year** — on the same 2025 roster but did not play a snap
""")

# ════════════════════════════════
# TAB 2 — Team View
# ════════════════════════════════
with tab2:
    st.subheader("Team View")
    selected_team = st.selectbox("Select Team", sorted(merged["team"].unique()))

    team_ol = merged[merged["team"] == selected_team].copy()

    # Position order left to right
    pos_order = ["LT","LG","C","RG","RT"]
    pos_labels = {"LT":"Left Tackle","LG":"Left Guard","C":"Center","RG":"Right Guard","RT":"Right Tackle"}
    team_ol["pos_order"] = team_ol["pos_abb"].map({p:i for i,p in enumerate(pos_order)})
    team_ol = team_ol.sort_values("pos_order")

    fig = go.Figure()

    for _, row in team_ol.iterrows():
        is_incumbent = row["designation"] == "Returning Starter"
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

        # Rookie tag
        if is_rookie:
            fig.add_shape(type="rect", x0=x_pos-0.45, x1=x_pos+0.45, y0=0.08, y1=0.22,
                fillcolor="#2ECC71", line=dict(color="white", width=2))
            fig.add_annotation(x=x_pos, y=0.15, text="<b>ROOKIE</b>",
                showarrow=False, font=dict(size=13, color="white"), align="center")

        # Full-time Jump tag
        if row["designation"] == "Full-time Jump":
            fig.add_shape(type="rect", x0=x_pos-0.45, x1=x_pos+0.45, y0=0.08, y1=0.22,
                fillcolor="#3498DB", line=dict(color="white", width=2))
            fig.add_annotation(x=x_pos, y=0.15, text="<b>FULL-TIME JUMP</b>",
                showarrow=False, font=dict(size=11, color="white"), align="center")

        # Free Agent / Trade tag
        if row["designation"] == "Free Agent / Trade":
            fig.add_shape(type="rect", x0=x_pos-0.45, x1=x_pos+0.45, y0=0.08, y1=0.22,
                fillcolor="#9B59B6", line=dict(color="white", width=2))
            fig.add_annotation(x=x_pos, y=0.15, text="<b>FREE AGENT / TRADE</b>",
                showarrow=False, font=dict(size=11, color="white"), align="center")

        # Missed Year tag
        if row["designation"] == "Missed Year":
            fig.add_shape(type="rect", x0=x_pos-0.45, x1=x_pos+0.45, y0=0.08, y1=0.22,
                fillcolor="#E67E22", line=dict(color="white", width=2))
            fig.add_annotation(x=x_pos, y=0.15, text="<b>MISSED YEAR</b>",
                showarrow=False, font=dict(size=11, color="white"), align="center")

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
    col1.markdown("🔵 **Returning Starter** — took more than 50% snaps or started Week 1 on same team in 2025")
    col2.markdown("🟡 **New Starter** — does not meet threshold for Returning Starter status")

# ════════════════════════════════
# TAB 3 — League Overview
# ════════════════════════════════
with tab3:
    st.subheader("2026 League-Wide OL Continuity Overview")

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
        color_map = {
            "Returning Starter": "#378ADD",
            "Full-time Jump":    "#3498DB",
            "Free Agent / Trade":   "#9B59B6",
            "Rookie":            "#2ECC71",
            "Missed Year":       "#E67E22"
        }
        fig_pie = px.pie(
            des_counts, values="Count", names="Designation",
            title="League-Wide OL Starter Breakdown",
            color="Designation",
            color_discrete_map=color_map
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    

   # Returning Starter bucket table
    st.subheader("Starting OL Continuity: Total Returning Starters in 2026")
    st.caption("Returning Starters = took more than 50% snaps or started Week 1 on same team last year.")

    col_colors = {"0":"#8B0000","1":"#CC3333","2":"#e07b7b","3":"#FFD580","4":"#90D4B5","5":"#1D9E75"}

    buckets = {i: [] for i in range(6)}
    for _, row in team_summary.iterrows():
        buckets[int(row["incumbents"])].append(row["team"])

    max_len = max(len(v) for v in buckets.values())
    bucket_df = pd.DataFrame({
        str(i): buckets[i] + [""] * (max_len - len(buckets[i]))
        for i in range(6)
    })

    def style_buckets(col):
        return [
            f"background-color: {col_colors.get(col.name, 'white')}; color: white; font-weight: bold; text-align: center"
            if v != "" else ""
            for v in col
        ]

    styled_bucket = bucket_df.style.apply(style_buckets, axis=0)

    st.dataframe(styled_bucket, use_container_width=True, hide_index=True,
                 height=(max_len + 1) * 35 + 10)
    
    # Rookie starters by team
    st.subheader("Rookie Offensive Linemen Projected to Start Week 1")
    rookies = merged[merged["designation"] == "Rookie"][["team","player_name","pos_abb"]].sort_values("team")
    if len(rookies) > 0:
        st.dataframe(rookies.rename(columns={"team":"Team","player_name":"Player","pos_abb":"Position"}).reset_index(drop=True),
                     use_container_width=True, hide_index=True)
    else:
        st.write("No rookie starters found.")

    st.divider()

    # ════════════════════════════════
# TAB 4 — Historical OL Continuity
# ════════════════════════════════
with tab4:
    st.subheader("OL Continuity & Offensive Production: 2020–2025")
    st.caption("Returning Starter = took 50%+ regular season offensive snaps OR started Week 1 for same team the prior season")

    @st.cache_data
    def load_historical():
        hist = pd.read_csv("ol_historical.csv")
        hist["team"] = hist["team"].replace({"LA": "LAR"})
        import openpyxl
        wb = openpyxl.load_workbook("starting_OL_continuity_book_2020-2025.xlsx")
        starters_rows = []
        for season in range(2020, 2026):
            ws = wb[str(season)]
            header_row = None
            for row in ws.iter_rows():
                for cell in row:
                    if cell.value == "Team":
                        header_row = cell.row
                        break
                if header_row:
                    break
            for row in ws.iter_rows(min_row=header_row+1):
                team = row[0].value
                if not team or len(str(team)) > 5:
                    break
                for i, pos in enumerate(["LT","LG","C","RG","RT"]):
                    cell = row[i+1]
                    if cell.value is None:
                        continue
                    is_red = False
                    if cell.font and cell.font.color and cell.font.color.type == 'rgb':
                        color = cell.font.color.rgb.upper()
                        if color in ['FFFF0000', 'FF0000']:
                            is_red = True
                    starters_rows.append({
                        "team": team,
                        "season": season,
                        "pos": pos,
                        "player": cell.value,
                        "returning": not is_red
                    })
        starters_df = pd.DataFrame(starters_rows)
        return hist, starters_df

    hist_df, starters_df = load_historical()

    # Year range slider
    min_year, max_year = int(hist_df["season"].min()), int(hist_df["season"].max())
    year_range = st.slider("Select Season Range", min_year, max_year, (min_year, max_year))
    filtered = hist_df[(hist_df["season"] >= year_range[0]) & (hist_df["season"] <= year_range[1])]

    # Team filter
    all_teams = sorted(hist_df["team"].unique())
    selected_teams = st.multiselect("Filter by Team (leave blank for all)", all_teams, default=[])

    # Aggregate ALL teams first
    n_seasons = year_range[1] - year_range[0] + 1
    agg = filtered.groupby("team").agg(
        avg_returning_starters=("returning_starters","mean"),
        total_yards=("total_yards","sum"),
    ).reset_index()
    agg["avg_returning_starters"] = agg["avg_returning_starters"].round(2)
    agg["avg_yards_per_season"] = (agg["total_yards"] / n_seasons).round(0).astype(int)
    agg["total_yards_rank"] = agg["total_yards"].rank(ascending=False).astype(int)
    agg["total_yards"] = agg["total_yards"].astype(int)
    agg = agg.sort_values("total_yards_rank")

    # Filter for display if teams selected
    display_agg = agg[agg["team"].isin(selected_teams)] if selected_teams else agg

    st.dataframe(
        display_agg[["team","avg_returning_starters","total_yards","total_yards_rank","avg_yards_per_season"]].rename(columns={
            "team": "Team",
            "avg_returning_starters": "Avg Returning Starters",
            "total_yards": "Total Yards",
            "total_yards_rank": "Total Yards Rank",
            "avg_yards_per_season": "Avg Yards/Season"
        }).reset_index(drop=True),
        use_container_width=True, hide_index=True
    )

    st.caption("*Yards = total offense during regular season.*")
    if selected_teams:
        # Team view
        st.subheader("Returning Starters Over Time")
        team_filtered = filtered[filtered["team"].isin(selected_teams)]
        fig_line = px.line(
            team_filtered,
            x="season", y="returning_starters",
            color="team",
            markers=True,
            labels={"season": "Season", "returning_starters": "Returning Starters", "team": "Team"},
            title="Returning OL Starters by Season"
        )
        fig_line.update_layout(
            yaxis=dict(range=[0,5.5], dtick=1),
            height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # OL lineup grid by year
        st.subheader("Week 1 Starting OL by Season")
        positions = ["LT","LG","C","RG","RT"]

        for team in selected_teams:
            if len(selected_teams) > 1:
                st.markdown(f"**{team}**")
            team_starters = starters_df[
                (starters_df["team"] == team) &
                (starters_df["season"] >= year_range[0]) &
                (starters_df["season"] <= year_range[1])
            ]
            seasons_shown = sorted(team_starters["season"].unique(), reverse=True)

            fig_grid = go.Figure()

            # Position headers at top
            for col_idx, pos in enumerate(positions):
                fig_grid.add_shape(
                    type="rect",
                    x0=col_idx - 0.45, x1=col_idx + 0.45,
                    y0=-0.45, y1=0.45,
                    fillcolor="rgba(200,200,200,0.95)",
                    line=dict(color="white", width=2)
                )
                fig_grid.add_annotation(
                    x=col_idx, y=0,
                    text=f"<b>{pos}</b>",
                    showarrow=False,
                    font=dict(size=32, color="#111111"),
                    align="center"
                )
                

            for row_idx, szn in enumerate(seasons_shown):
                szn_data = team_starters[team_starters["season"] == szn]
                y_pos = -(row_idx + 1)

                # Year label
                fig_grid.add_annotation(
                    x=-0.8, y=y_pos,
                    text=f"<b>{szn}</b>",
                    showarrow=False,
                    font=dict(size=24, color="#333333"),
                    align="center",
                    bgcolor="rgba(220,220,220,0.9)",
                    borderpad=18
                )

                for col_idx, pos in enumerate(positions):
                    player_row = szn_data[szn_data["pos"] == pos]
                    if len(player_row) == 0:
                        continue
                    player = player_row.iloc[0]["player"]
                    returning = player_row.iloc[0]["returning"]
                    color = "#378ADD" if returning else "#FFD580"
                    text_color = "white" if returning else "black"

                    fig_grid.add_shape(
                        type="rect",
                        x0=col_idx - 0.45, x1=col_idx + 0.45,
                        y0=y_pos - 0.45, y1=y_pos + 0.45,
                        fillcolor=color,
                        line=dict(color="white", width=1)
                    )
                    fig_grid.add_annotation(
                        x=col_idx, y=y_pos,
                        text=f"<b>{player}</b>",
                        showarrow=False,
                        font=dict(size=26, color=text_color),
                        align="center"
                    )

            n_rows = len(seasons_shown)
            fig_grid.update_layout(
                height=max(200, n_rows * 120 + 80),
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[-1.3, 4.6]),
                yaxis=dict(showticklabels=False, showgrid=False, zeroline=False,
                          range=[-(n_rows + 0.6), 0.6]),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False
            )
            st.plotly_chart(fig_grid, use_container_width=True)

