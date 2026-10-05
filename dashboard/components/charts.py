import streamlit as st
import pandas as pd

from services.api_client import get_events


def render_charts():
    events = get_events(limit=100)

    st.title("📊 Analytics")

    if not events:
        st.info("No analytics available.")
        return

    df = pd.DataFrame(events)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # -----------------------------
    # Event Distribution
    # -----------------------------
    st.subheader("Event Distribution")

    event_counts = (
        df["event_type"]
        .str.replace("_", " ")
        .str.title()
        .value_counts()
    )

    st.bar_chart(event_counts)

    st.divider()

    # -----------------------------
    # Events Over Time
    # -----------------------------
    st.subheader("Events Over Time")

    timeline = (
        df.set_index("timestamp")
        .resample("1min")
        .size()
    )

    st.line_chart(timeline)
