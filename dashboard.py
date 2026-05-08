import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from collections import defaultdict

# ── Page config ──
st.set_page_config(
    page_title="2026 NFL Draft Dashboard",
    page_icon="🏈",
    layout="wide"
)

# ── Load data ──
@st.cache_data
def load_data():
    df = pd.read_excel("NFL-Draft-Book-2026.xlsx")
    df.columns = ["selection","round","pick","team","player","pos","age","college",
                  "pick_value","consensus","consensus_value","value_diff"]
    # Normalize positions
    df["pos"] = df["pos"].replace({
        "OLB": "EDGE",
        "DE":  "EDGE",
        "OT":  "OL",
        "OL":  "OL",
        "C":   "OL",
        "G":   "OL",
        "OG":  "OL",
        "DL":  "DT",
        "NT":  "DT",
    })
    fs_chart = {
        1:3000,2:2649,3:2443,4:2297,5:2184,6:2092,7:2014,8:1946,
        9:1887,10:1833,11:1785,12:1741,13:1700,14:1663,15:1628,16:1595,
        17:1564,18:1535,19:1508,20:1482,21:1457,22:1434,23:1411,24:1389,
        25:1369,26:1349,27:1330,28:1311,29:1294,30:1276,31:1260,32:1244,
        33:1228,34:1213,35:1198,36:1184,37:1170,38:1157,39:1143,40:1131,
        41:1118,42:1106,43:1094,44:1082,45:1071,46:1060,47:1049,48:1039,
        49:1028,50:1018,51:1008,52:999,53:989,54:980,55:971,56:962,
        57:953,58:944,59:936,60:927,61:919,62:911,63:903,64:895,
        65:888,66:880,67:873,68:865,69:858,70:851,71:844,72:837,
        73:831,74:824,75:817,76:811,77:805,78:798,79:792,80:786,
        81:780,82:774,83:768,84:762,85:757,86:751,87:745,88:740,
        89:735,90:729,91:724,92:719,93:713,94:708,95:703,96:698,
        97:694,98:689,99:684,100:679,101:675,102:670,103:665,104:661,
        105:656,106:652,107:647,108:643,109:639,110:634,111:630,112:626,
        113:622,114:617,115:613,116:609,117:605,118:601,119:597,120:594,
        121:590,122:586,123:582,124:579,125:575,126:571,127:568,128:564,
        129:561,130:557,131:554,132:550,133:547,134:543,135:540,136:537,
        137:533,138:530,139:527,140:524,141:520,142:517,143:514,144:511,
        145:508,146:505,147:502,148:499,149:496,150:493,151:490,152:487,
        153:484,154:482,155:479,156:476,157:473,158:471,159:468,160:465,
        161:463,162:460,163:458,164:455,165:453,166:450,167:448,168:445,
        169:443,170:441,171:438,172:436,173:434,174:431,175:429,176:427,
        177:425,178:422,179:420,180:418,181:416,182:414,183:412,184:410,
        185:407,186:405,187:403,188:401,189:399,190:397,191:395,192:393,
        193:392,194:390,195:388,196:386,197:384,198:382,199:381,200:379,
        201:377,202:375,203:374,204:372,205:370,206:368,207:367,208:365,
        209:363,210:362,211:360,212:358,213:357,214:355,215:353,216:352,
        217:350,218:349,219:347,220:345,221:344,222:342,223:341,224:339,
        225:338,226:336,227:335,228:333,229:332,230:330,231:329,232:327,
        233:326,234:325,235:323,236:322,237:320,238:319,239:317,240:316,
        241:315,242:313,243:312,244:310,245:309,246:308,247:306,248:305,
        249:303,250:302,251:301,252:299,253:298,254:297,255:295,256:294,
        257:293
    }

    FUTURE_7 = 280
    FUTURE_6 = 230
    FUTURE_4 = 550
    FUTURE_3 = 720

    def v(pick):
        return fs_chart.get(pick, 0)

    trades = [
        ("CLE",[v(6)],[v(9),v(74),v(148)]),
        ("KAN",[v(9),v(74),v(148)],[v(6)]),
        ("MIA",[v(11)],[v(12),v(177),v(180)]),
        ("DAL",[v(12),v(177),v(180)],[v(11)]),
        ("DAL",[v(20),FUTURE_7],[v(23),v(114),v(137)]),
        ("PHI",[v(23),v(114),v(137)],[v(20),FUTURE_7]),
        ("BUF",[v(26),v(91)],[v(28),v(69),v(167)]),
        ("HOU",[v(28),v(69),v(167)],[v(26),v(91)]),
        ("SFO",[v(27),v(138)],[v(30),v(90)]),
        ("MIA",[v(30),v(90)],[v(27),v(138)]),
        ("BUF",[v(28)],[v(31),v(125)]),
        ("NWE",[v(31),v(125)],[v(28)]),
        ("SFO",[v(30)],[v(33),v(179)]),
        ("NYJ",[v(33),v(179)],[v(30)]),
        ("BUF",[v(31),v(69),v(165)],[v(35),v(66),v(101)]),
        ("TEN",[v(35),v(66),v(101)],[v(31),v(69),v(165)]),
        ("LVR",[v(36),v(117)],[v(38),v(91)]),
        ("HOU",[v(38),v(91)],[v(36),v(117)]),
        ("NYJ",[v(44)],[v(50),v(128)]),
        ("DET",[v(50),v(128)],[v(44)]),
        ("IND",[v(47),v(249)],[v(53),v(135),v(237)]),
        ("PIT",[v(53),v(135),v(237)],[v(47),v(249)]),
        ("MIN",[v(49),v(196)],[v(51),v(159)]),
        ("CAR",[v(51),v(159)],[v(49),v(196)]),
        ("LAC",[v(55)],[v(63),v(131),v(202)]),
        ("NWE",[v(63),v(131),v(202)],[v(55)]),
        ("SFO",[v(58),v(152)],[v(70),v(107)]),
        ("CLE",[v(70),v(107)],[v(58),v(152)]),
        ("CHI",[v(60)],[v(69),v(144)]),
        ("TEN",[v(69),v(144)],[v(60)]),
        ("DEN",[v(62)],[v(66),v(182)]),
        ("BUF",[v(66),v(182)],[v(62)]),
        ("CLE",[v(74)],[v(105),v(145),FUTURE_4]),
        ("NYG",[v(105),v(145),FUTURE_4],[v(74)]),
        ("TAM",[v(77)],[v(84),v(160)]),
        ("GNB",[v(84),v(160)],[v(77)]),
        ("LAC",[v(86)],[v(105),v(145),v(206)]),
        ("CLE",[v(105),v(145),v(206)],[v(86)]),
        ("SEA",[v(96)],[v(99),v(216)]),
        ("PIT",[v(99),v(216)],[v(96)]),
        ("DAL",[v(152)],[0]),
        ("SFO",[0],[v(152)]),
        ("MIN",[v(244)],[v(98),FUTURE_3]),
        ("PHI",[v(98),FUTURE_3],[v(244)]),
        ("BUF",[v(101)],[v(102),FUTURE_7]),
        ("LVR",[v(102),FUTURE_7],[v(101)]),
        ("CIN",[v(110),v(199)],[v(128),v(140)]),
        ("NYJ",[v(128),v(140)],[v(110),v(199)]),
        ("HOU",[v(117)],[v(123),v(204)]),
        ("LAC",[v(123),v(204)],[v(117)]),
        ("CAR",[v(119),v(196)],[v(124),v(166)]),
        ("JAX",[v(124),v(166)],[v(119),v(196)]),
        ("ATL",[v(122)],[v(134),v(208)]),
        ("LVR",[v(134),v(208)],[v(122)]),
        ("CAR",[v(124),v(166)],[v(129),v(144)]),
        ("CHI",[v(129),v(144)],[v(124),v(166)]),
        ("SFO",[v(133)],[v(154),FUTURE_6]),
        ("BAL",[v(154),FUTURE_6],[v(133)]),
        ("CLE",[v(148)],[FUTURE_4]),
        ("SEA",[FUTURE_4],[v(148)]),
        ("MIA",[v(151),v(227)],[v(158),v(200)]),
        ("CAR",[v(158),v(200)],[v(151),v(227)]),
        ("CLE",[v(152)],[v(170),v(182)]),
        ("DEN",[v(170),v(182)],[v(152)]),
        ("PIT",[v(161),v(249)],[v(169),v(210)]),
        ("KAN",[v(169),v(210)],[v(161),v(249)]),
        ("BUF",[v(168)],[v(181),v(213)]),
        ("DET",[v(181),v(213)],[v(168)]),
        ("LVR",[v(185)],[v(195),v(229)]),
        ("TAM",[v(195),v(229)],[v(185)]),
        ("SEA",[v(188)],[v(199),v(242)]),
        ("NYJ",[v(199),v(242)],[v(188)]),
        ("NWE",[v(191)],[v(196),v(245)]),
        ("JAX",[v(196),v(245)],[v(191)]),
        ("PHI",[v(197)],[v(207),v(251),v(252)]),
        ("LAR",[v(207),v(251),v(252)],[v(197)]),
        ("NWE",[v(198)],[v(234),FUTURE_6]),
        ("MIN",[v(234),FUTURE_6],[v(198)]),
        ("BUF",[v(213)],[v(239),v(241)]),
        ("CHI",[v(239),v(241)],[v(213)]),
        ("SEA",[v(216)],[v(236),v(255)]),
        ("GNB",[v(236),v(255)],[v(216)]),
        ("LVR",[v(219)],[v(150)]),
        ("NOR",[v(150)],[v(219)]),
    ]

    trade_net = defaultdict(float)
    for team, sent, received in trades:
        trade_net[team] += sum(received) - sum(sent)

    # Only use rounds 1-5 for threshold calculation
    all_ranked = df[df["round"] <= 5].dropna(subset=["value_diff"])
    mean_vd = all_ranked["value_diff"].mean()
    std_vd = all_ranked["value_diff"].std()
    value_threshold = mean_vd + std_vd
    reach_threshold = mean_vd - std_vd

    def tag(row):
        # Rounds 6-7 are excluded entirely
        if row["round"] >= 6:
            return "excluded"
        # Rounds 1-5 unranked = reach
        if pd.isna(row["value_diff"]):
            return "reach"
        if row["value_diff"] >= value_threshold:
            return "value"
        if row["value_diff"] <= reach_threshold:
            return "reach"
        return "consensus"

    df["pick_tag"] = df.apply(tag, axis=1)

    def assign_grade(score):
        if score < 1:   return "F-"
        if score < 2:   return "F"
        if score < 3:   return "D"
        if score < 4:   return "C"
        if score < 5:   return "C+"
        if score < 6:   return "B-"
        if score < 7:   return "B"
        if score < 8:   return "B+"
        if score < 9:   return "A"
        if score < 9.6: return "A+"
        return "A+"

    teams = sorted(df["team"].unique())
    summary = []
    for team in teams:
        tdf = df[df["team"] == team]
        ranked = tdf[tdf["round"] <= 5].dropna(subset=["value_diff"])
        n = len(ranked)
        total_vd  = ranked["value_diff"].sum() if n > 0 else 0
        avg_vd    = ranked["value_diff"].mean() if n > 0 else 0
        trade_cap = trade_net.get(team, 0)
        adj_total = total_vd + trade_cap
        adj_avg   = (adj_total / n) if n > 0 else 0

        # Rate calculations exclude rounds 6-7 and count unranked r1-5 as reach
        rate_picks = tdf[tdf["round"] <= 5]
        rate_picks = rate_picks.copy()
        rate_picks["tag"] = rate_picks.apply(tag, axis=1)
        tags = rate_picks["tag"].value_counts()
        total_tagged = tags.get("value",0) + tags.get("reach",0) + tags.get("consensus",0)
        value_rate     = round(tags.get("value",0)     / total_tagged * 100, 1) if total_tagged > 0 else 0
        reach_rate     = round(tags.get("reach",0)     / total_tagged * 100, 1) if total_tagged > 0 else 0
        consensus_rate = round(tags.get("consensus",0) / total_tagged * 100, 1) if total_tagged > 0 else 0
        value_edge     = round(value_rate - reach_rate, 1)

        summary.append({
            "team": team,
            "ranked_picks": n,
            "total_value_diff": round(total_vd),
            "avg_value_diff": round(avg_vd, 1),
            "trade_capital_net": round(trade_cap),
            "adj_total": round(adj_total),
            "adj_avg": round(adj_avg, 1),
            "value_rate": value_rate,
            "reach_rate": reach_rate,
            "consensus_rate": consensus_rate,
            "value_edge": value_edge
        })

    summary_df = pd.DataFrame(summary)

    min_adj = summary_df["adj_avg"].min()
    max_adj = summary_df["adj_avg"].max()
    summary_df["score"] = ((summary_df["adj_avg"] - min_adj) / (max_adj - min_adj) * 10).round(1)
    summary_df["grade"] = summary_df["score"].apply(assign_grade)

    min_tv = summary_df["total_value_diff"].min()
    max_tv = summary_df["total_value_diff"].max()
    summary_df["total_score"] = ((summary_df["adj_total"] - min_tv) / (max_tv - min_tv) * 10).round(1)
    summary_df["total_grade"] = summary_df["total_score"].apply(assign_grade)

    return df, summary_df


df, summary_df = load_data()

# ── Header ──
st.title("🏈 2026 NFL Draft Dashboard")
st.markdown("*Draft slot valuations via the Fitzgerald-Spielberger chart and consensus big board rankings via Arif Hasan*")
st.divider()

# ── Sidebar ──
st.sidebar.title("Filters")
selected_team  = st.sidebar.selectbox("Team",     ["All"] + sorted(df["team"].unique().tolist()))
selected_pos   = st.sidebar.selectbox("Position", ["All"] + sorted(df["pos"].dropna().unique().tolist()))
selected_round = st.sidebar.selectbox("Round",    ["All"] + list(range(1, 8)))

# ── Filter picks ──
filtered = df.copy()
if selected_team  != "All": filtered = filtered[filtered["team"]  == selected_team]
if selected_pos   != "All": filtered = filtered[filtered["pos"]   == selected_pos]
if selected_round != "All": filtered = filtered[filtered["round"] == selected_round]

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs(["📊 Team Grades", "🔵 YMMV Quadrants", "📋 Pick Explorer", "🏆 Bucking Consensus"])

# ════════════════════════════════
# TAB 1 — Team Grades
# ════════════════════════════════
with tab1:
    st.subheader("Team Draft Grades")
    st.markdown("Grades reflect the total value per Fitzgerald-Spielberger chart that teams generated during 2026 NFL Draft weekend.")
    display_cols = ["team","total_value_diff","trade_capital_net",
                "adj_total","score","grade","value_rate","reach_rate","consensus_rate"]

    styled = summary_df[display_cols].rename(columns={
        "team":             "Team",
        "total_value_diff": "Pick Value Net",
        "trade_capital_net":"Trade Value Net",
        "adj_total":        "Adj Total",
        "score":            "Score",
        "grade":            "Grade",
        "value_rate":       "Value Rate",
        "reach_rate":       "Reach Rate",
        "consensus_rate":   "Consensus Rate"
    }).sort_values("Score", ascending=False).reset_index(drop=True)

    def style_table(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        # Bold first row
        styles.iloc[0] = "font-weight: bold"
        # Bold first column
        styles.iloc[:, 0] = "font-weight: bold"
        # Center all columns except first
        for col in df.columns[1:]:
            styles[col] = styles[col] + "; text-align: center"
        return styles

    st.dataframe(
        styled.style.apply(style_table, axis=None),
        use_container_width=True,
        hide_index=True
    )
    st.markdown("Each draft slot is attributed points via the Fitzgerald-Spielberger chart and consensus mock draft slot comes from Arif Hasan's consensus mock draft board. Adj. Avg maps directly to Grades and is the amount of Fitzgerald-Spielberger points divided by board-ranked picks made by each team. Points and the resulting grade are an aggregate of points from 1) pick # for player relative to mock draft consensus board # 2) trade net on pure pick swap deals.")


# ════════════════════════════════
# TAB 2 — YMMV Quadrants
# ════════════════════════════════
with tab2:
    st.subheader("Trade Capital vs Player Selection Value")

    def quadrant_color(row):
        if row["trade_capital_net"] >= 0 and row["total_value_diff"] >= 0:
            return "Caught Value / Gained Picks"
        if row["trade_capital_net"] <  0 and row["total_value_diff"] >= 0:
            return "Caught Value / Lost Picks"
        if row["trade_capital_net"] >= 0 and row["total_value_diff"] <  0:
            return "Reached / Gained Picks"
        return "Reached / Lost Picks"

    summary_df["quadrant"] = summary_df.apply(quadrant_color, axis=1)

    color_map = {
        "Caught Value / Gained Picks": "#1D9E75",
        "Caught Value / Lost Picks":   "#378ADD",
        "Reached / Gained Picks":      "#BA7517",
        "Reached / Lost Picks":        "#CC3333"
    }

    fig = px.scatter(
        summary_df,
        x="trade_capital_net",
        y="total_value_diff",
        color="quadrant",
        color_discrete_map=color_map,
        hover_data=["grade","adj_avg","value_edge"],
        title="2026 NFL Draft — Trade Capital vs Total Player Selection Value",
        labels={
            "trade_capital_net": "Trade Capital Net (F-S Points*)",
            "total_value_diff":  "Total Pick Value Diff vs Board (F-S Points*)"
        }
    )

    fig.update_traces(marker=dict(size=12))
    fig.add_hline(y=0, line_width=1, line_color="black")
    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.update_layout(height=600)

    # Team labels with manual nudge for WAS/CAR overlap
    for _, row in summary_df.iterrows():
        if row["team"] == "WAS":
            fig.add_annotation(
                x=row["trade_capital_net"],
                y=row["total_value_diff"],
                text="WAS",
                ax=0, ay=-15,
                font=dict(size=9, color="black"),
                bgcolor="rgba(255,255,255,0.7)"
            )
        elif row["team"] == "CAR":
            fig.add_annotation(
                x=row["trade_capital_net"],
                y=row["total_value_diff"],
                text="CAR",
                ax=0, ay=-25,
                font=dict(size=9, color="black"),
                bgcolor="rgba(255,255,255,0.7)"
            )
        else:
            fig.add_annotation(
                x=row["trade_capital_net"],
                y=row["total_value_diff"],
                text=row["team"],
                showarrow=False,
                yshift=12,
                font=dict(size=9, color="black"),
                bgcolor="rgba(255,255,255,0.7)"
            )

    # Quadrant labels
    x_min = summary_df["trade_capital_net"].min()
    x_max = summary_df["trade_capital_net"].max()
    y_min = summary_df["total_value_diff"].min()
    y_max = summary_df["total_value_diff"].max()

    quadrant_labels = [
        (x_max * 0.75, y_max * 0.90, "Caught Value on Consensus Board<br>Gained Value on Pick Swaps", "#1D9E75"),
        (x_min * 0.65, y_max * 0.98, "Caught Value on Consensus Board<br>Lost Value on Pick Swaps",   "#378ADD"),
        (x_max * 0.75, y_min * 0.80, "Reached vs Consensus Board<br>Gained Value on Pick Swaps",      "#BA7517"),
        (x_min * 0.75, y_min * 0.80, "Reached vs Consensus Board<br>Lost Value on Pick Swaps",        "#CC3333"),
    ]

    for x, y, text, color in quadrant_labels:
        fig.add_annotation(
            x=x, y=y, text=text,
            showarrow=False,
            font=dict(size=12, color=color, family="Arial Black"),
            align="center",
            bgcolor="rgba(255,255,255,0.75)",
            borderpad=4
        )

    fig.add_annotation(
        text="*F-S Points = Draft slot value via the Fitzgerald-Spielberger chart",
        xref="paper", yref="paper", x=0, y=-0.12,
        showarrow=False, font=dict(size=10, color="gray")
    )

    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════
# TAB 3 — Pick Explorer
# ════════════════════════════════
with tab3:
    st.subheader("Pick Explorer")
    if selected_team != "All":
        st.markdown(f"Showing **{selected_team}** picks")
    else:
        st.markdown("Use sidebar to filter by team, position, or round")

    show_cols = ["selection","round","pick","team","player","pos", "pick_tag", "age",
                 "college","pick_value","consensus","consensus_value","value_diff"]

    st.dataframe(
        filtered[show_cols].rename(columns={"pick_tag": "rel_mocks"}).sort_values("selection").reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

    if selected_team != "All":
        team_row = summary_df[summary_df["team"] == selected_team].iloc[0]

        board_rank = summary_df["total_value_diff"].rank(ascending=False).loc[
            summary_df["team"] == selected_team
        ].iloc[0]
        trade_rank = summary_df["trade_capital_net"].rank(ascending=False).loc[
            summary_df["team"] == selected_team
        ].iloc[0]
        total_teams = len(summary_df)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Grade",                    team_row["grade"])
        col2.metric("Score",                    team_row["score"])
        col3.metric("Value on Board Rank", f"{int(board_rank)} of {total_teams}")
        col4.metric("Value on Pick Swap Rank",                f"{int(trade_rank)} of {total_teams}")

# ════════════════════════════════
# TAB 4 — Bucking Consensus
# ════════════════════════════════
with tab4:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🟢 Top 10 Value Picks")
        top_value = df.dropna(subset=["value_diff"]).sort_values("value_diff", ascending=False).head(10)
        st.dataframe(
            top_value[["selection","team","player","pos","consensus","value_diff"]].reset_index(drop=True),
            use_container_width=True, hide_index=True
        )

    with col2:
        st.subheader("🔴 Top 10 Reaches")
        top_reach = df.dropna(subset=["value_diff"]).sort_values("value_diff").head(10)
        st.dataframe(
            top_reach[["selection","team","player","pos","consensus","value_diff"]].reset_index(drop=True),
            use_container_width=True, hide_index=True
        )

    st.divider()
    
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.subheader("Value Rate by Team")
        fig_vr = px.bar(
            summary_df.sort_values("value_rate", ascending=True),
            x="value_rate", y="team", orientation="h",
            color="value_rate",
            color_continuous_scale=["#ffffff","#1D9E75"],
            labels={"value_rate": "Value Rate (%)", "team": "Team"}
        )
        fig_vr.update_layout(height=700, coloraxis_showscale=False)
        st.plotly_chart(fig_vr, use_container_width=True)

    with col_b:
        st.subheader("Consensus Rate by Team")
        fig_cr = px.bar(
            summary_df.sort_values("consensus_rate", ascending=True),
            x="consensus_rate", y="team", orientation="h",
            color="consensus_rate",
            color_continuous_scale=["#ffffff","#378ADD"],
            labels={"consensus_rate": "Consensus Rate (%)", "team": "Team"}
        )
        fig_cr.update_layout(height=700, coloraxis_showscale=False)
        st.plotly_chart(fig_cr, use_container_width=True)

    with col_c:
        st.subheader("Reach Rate by Team")
        fig_rr = px.bar(
            summary_df.sort_values("reach_rate", ascending=True),
            x="reach_rate", y="team", orientation="h",
            color="reach_rate",
            color_continuous_scale=["#ffffff","#CC3333"],
            labels={"reach_rate": "Reach Rate (%)", "team": "Team"}
        )
        fig_rr.update_layout(height=700, coloraxis_showscale=False)
        st.plotly_chart(fig_rr, use_container_width=True)
    st.divider()
    st.markdown("""
**Reach Rate** — percentage of picks selected well ahead of their consensus board ranking.  
**Consensus Rate** — percentage of picks selected in line with their consensus board ranking.  
**Value Rate** — percentage of picks selected much later than their consensus board ranking.  
*Threshold: one standard deviation or more from the mean value differential across all ranked picks.*
""")

    st.divider()
    st.subheader("Position Tendencies vs Board — Rounds 1-3 (All Teams)")

    pos_all = df[
        (df["round"] <= 3) &
        (df["value_diff"].notna())
    ].groupby("pos").agg(
        picks=("player", "count"),
        avg_value_diff=("value_diff", "mean")
    ).reset_index()

    pos_all["avg_value_diff"] = pos_all["avg_value_diff"].round(0)
    pos_all = pos_all.sort_values("avg_value_diff")

    fig_pos_all = px.bar(
        pos_all,
        x="avg_value_diff", y="pos", orientation="h",
        color="avg_value_diff",
        color_continuous_scale=["#CC3333","#ffffff","#1D9E75"],
        text="picks",
        title="Avg Value Diff by Position — Rounds 1-3 (League Wide)",
        labels={"avg_value_diff": "Avg Value Diff (F-S Points)", "pos": "Position", "picks": "# Picks"}
    )
    fig_pos_all.update_traces(textposition="outside")
    fig_pos_all.add_vline(x=0, line_width=1, line_color="black")
    fig_pos_all.update_layout(height=500, coloraxis_showscale=False)
    st.plotly_chart(fig_pos_all, use_container_width=True)
    st.divider()
    st.markdown("*Red indicates teams were more bullish on that position than consensus big board; Green indicates less bullish.*")