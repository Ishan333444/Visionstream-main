import streamlit as st

st.set_page_config(page_title="About", layout="wide")

st.title("ℹ️ VisionStream")

st.markdown("""
## Real-Time AI Surveillance Platform

VisionStream is a modular surveillance system built for real-time video analytics.

### Features

- 👤 Person Detection & Tracking
- ➡️ Entry Counting
- ⬅️ Exit Counting
- 🚨 Intrusion Detection
- ⏱ Dwell Time Monitoring
- 👥 Crowd Density Estimation
- 🔥 Heatmap Generation
- 📊 Live Dashboard
- 🗄 SQLite Database
- 🌐 FastAPI Backend

---

### Tech Stack

- Python
- OpenCV
- YOLO
- FastAPI
- SQLite
- Streamlit
""")
