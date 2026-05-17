import streamlit as st
# Home
st.set_page_config(page_title="Viztas", page_icon="📊", layout="wide")
st.markdown("""
    <style>
    [data-testid="stSidebarNavItems"] li:first-child {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)
st.title("📊 Viztas")
st.markdown("### A collection of apps from the data science lens of Thomas Emerick")
st.divider()

st.sidebar.markdown("# 🏠 Home")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="background-color:#1D9E75; padding:30px; border-radius:10px; height:200px;">
        <h2 style="color:white; margin-top:0;">🏈 NFL Draft 2026</h2>
        <p style="color:white;">Pick value, trade capital, and team grades for the 2026 NFL Draft using the Fitzgerald-Spielberger curve.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_NFL_Draft.py", label="→ Open NFL Draft Dashboard")

with col2:
    st.markdown("""
    <div style="background-color:#378ADD; padding:30px; border-radius:10px; height:200px;">
        <h2 style="color:white; margin-top:0;">🔵 NFL OL Continuity</h2>
        <p style="color:white;">2026 projected starting offensive lines, stability analysis, and historical trends since 2020.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_OL_Continuity.py", label="→ Open OL Continuity Dashboard")