import streamlit as st

from components.charts import render_charts

st.set_page_config(
    page_title="Analytics",
    layout="wide"
)

st.title("📊 Analytics")

render_charts()
