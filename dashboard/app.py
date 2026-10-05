import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from services.api_client import (
    get_health,
    get_stats,
    get_events,
)

from config import PAGE_TITLE, PAGE_ICON
from components.metrics import render_metrics
from components.event_table import render_event_table


st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
)

# Refresh dashboard every second
st_autorefresh(interval=1000, key="refresh")

st.title("🎥 VisionStream")
st.caption("Real-Time AI Surveillance & Analytics Dashboard")

st.divider()


# Check backend/engine health first
try:
    health = get_health()
    engine_healthy = health.get("status") == "healthy"

except requests.RequestException:
    engine_healthy = False


# Do not fetch dashboard data until the engine is healthy
if not engine_healthy:

    st.info(
        "⏳ VisionStream engine is starting. "
        "Dashboard data will appear once the engine is ready."
    )

    st.divider()

    status1, status2, status3 = st.columns(3)

    status1.metric(
        label="Backend",
        value="🟢 Online",
    )

    status2.metric(
        label="Engine",
        value="🟡 Starting",
    )

    status3.metric(
        label="Dashboard",
        value="🟡 Waiting",
    )

else:

    # Fetch dashboard data once per refresh
    stats = get_stats()
    events = get_events()

    # Dashboard metrics
    render_metrics(stats)

    st.divider()

    # System Status
    status1, status2, status3 = st.columns(3)

    status1.metric(
        label="Backend",
        value="🟢 Online",
    )

    status2.metric(
        label="Database",
        value="🟢 Connected",
    )

    status3.metric(
        label="People Detected",
        value=stats["people"],
    )

    st.divider()

    # Main layout
    left, right = st.columns(
        [3, 2],
        gap="large",
    )

    with left:
        st.subheader("📹 Live Feed")

        st.markdown(
            """
            The live video feed is available in a separate browser tab.

            Click below to view the real-time surveillance stream.
            """
        )

        st.link_button(
            "📹 Launch Live Feed",
            "http://127.0.0.1:8000/video_feed",
            use_container_width=True,
        )

    with right:
        render_event_table(events)