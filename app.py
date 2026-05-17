import streamlit as st

st.set_page_config(page_title="Viztas", page_icon="📊", layout="wide")

st.title("📊 datavizte")
st.markdown("### Data science applications by Thomas Emerick")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏈 2026 NFL Draft Analysis")
    st.markdown("Pick value, trade capital, and team grades for the 2026 NFL Draft.")
    st.page_link("pages/1_NFL_Draft.py", label="Open Draft Dashboard →")

with col2:
    st.subheader("🔵 NFL OL Continuity")
    st.markdown("2026 projected starting offensive lines, stability analysis, and historical trends.")
    st.page_link("pages/2_OL_Continuity.py", label="Open OL Dashboard →")