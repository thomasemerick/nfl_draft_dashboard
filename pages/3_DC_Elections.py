import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="DC Elections", page_icon="🗳️", layout="wide")
st.title("🗳️ DC Elections Dashboard")
st.caption("2026 Primary Intelligence — Ward-level analysis")

# Placeholder data — we'll replace with real DCBOE data
ward_data = pd.DataFrame({
    "Ward": [1, 2, 3, 4, 5, 6, 7, 8],
    "Registered_Dems": [32000, 28000, 30000, 35000, 38000, 36000, 33000, 30000],
    "Primary_Votes_2024": [8200, 7100, 9800, 9100, 8700, 9300, 6200, 5400],
    "Primary_Votes_2022": [7800, 6900, 9400, 8600, 8100, 8800, 5900, 5100],
    "Primary_Votes_2020": [10200, 8800, 11200, 10400, 9800, 10500, 7200, 6600],
})

ward_data["Turnout_2024_pct"] = (ward_data["Primary_Votes_2024"] / ward_data["Registered_Dems"] * 100).round(1)
ward_data["Opportunity"] = ward_data["Registered_Dems"] - ward_data["Primary_Votes_2024"]

# Metrics row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Registered Dems", f"{ward_data['Registered_Dems'].sum():,}")
col2.metric("2024 Primary Votes", f"{ward_data['Primary_Votes_2024'].sum():,}")
col3.metric("Avg Turnout", f"{ward_data['Turnout_2024_pct'].mean():.1f}%")
col4.metric("Untapped Voters", f"{ward_data['Opportunity'].sum():,}")

st.divider()

# Chart 1: Turnout trend
st.subheader("Primary Turnout by Ward: 2020–2024")
trend = ward_data[["Ward", "Primary_Votes_2020", "Primary_Votes_2022", "Primary_Votes_2024"]].melt(
    id_vars="Ward", var_name="Year", value_name="Votes"
)
trend["Year"] = trend["Year"].str.extract(r"(\d{4})")
fig1 = px.bar(trend, x="Ward", y="Votes", color="Year", barmode="group",
              color_discrete_map={"2020": "#003366", "2022": "#0066cc", "2024": "#66aaff"})
st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Opportunity Index
st.subheader("🎯 Opportunity Index — Registered Dems Who Didn't Vote (2024 Primary)")
st.caption("Voters a campaign should be targeting")
fig2 = px.bar(ward_data.sort_values("Opportunity", ascending=True),
              x="Opportunity", y="Ward", orientation="h",
              color="Opportunity", color_continuous_scale="Blues")
fig2.update_layout(yaxis=dict(tickvals=list(range(1,9)), ticktext=[f"Ward {i}" for i in range(1,9)]))
st.plotly_chart(fig2, use_container_width=True)

# Ward 1 Spotlight
st.subheader("📍 Ward 1 Spotlight — Trinidade Territory")
w1 = ward_data[ward_data["Ward"] == 1].iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Registered Dems", f"{w1['Registered_Dems']:,}")
c2.metric("2024 Primary Turnout", f"{w1['Turnout_2024_pct']}%")
c3.metric("Untapped Voters", f"{w1['Opportunity']:,}")