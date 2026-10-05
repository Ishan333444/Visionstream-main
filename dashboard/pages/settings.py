import streamlit as st

st.set_page_config(page_title="Settings", layout="wide")

st.title("⚙️ Settings")

confidence = st.slider(
    "Detection Confidence",
    0.1,
    1.0,
    0.5,
    0.05,
)

iou = st.slider(
    "IoU Threshold",
    0.1,
    1.0,
    0.5,
    0.05,
)

st.button("Save Settings")
