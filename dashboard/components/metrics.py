import streamlit as st

from services.api_client import get_stats


def render_metrics(stats):

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "👤 People",
        stats.get("people", 0)
    )

    col2.metric(
        "➡️ Entries",
        stats.get("entries", 0)
    )

    col3.metric(
        "⬅️ Exits",
        stats.get("exits", 0)
    )

    col4.metric(
        "🚨 Intrusions",
        stats.get("intrusions", 0)
    )

    col5.metric(
        "📋 Events",
        stats.get("total_events", 0)
    )
