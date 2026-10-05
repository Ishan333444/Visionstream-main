import streamlit as st
import pandas as pd


EVENT_ICONS = {
    "Line Entry": "🟢",
    "Line Exit": "🔴",
    "Entered Zone": "🟠",
    "Exited Zone": "🔵",
}


def render_event_table(all_events):
    # Use the first 20 events for the displayed table
    events = all_events[:20]

    st.subheader("📋 Recent Events")

    if not events:
        st.info("No events found.")
        return

    df = pd.DataFrame(events)
    export_df = pd.DataFrame(all_events)

    # Format both DataFrames identically
    for current_df in (df, export_df):

        current_df.rename(
            columns={
                "timestamp": "Time",
                "event_type": "Event",
                "track_id": "Track ID",
                "source": "Source",
            },
            inplace=True,
        )

        current_df["Time"] = (
            pd.to_datetime(current_df["Time"])
            .dt.strftime("%H:%M:%S")
        )

        current_df["Event"] = (
            current_df["Event"]
            .str.replace("_", " ")
            .str.title()
        )

        current_df["Source"] = (
            current_df["Source"]
            .str.replace("_", " ")
            .str.title()
        )

    # Filter only the displayed table
    event_filter = st.selectbox(
        "Filter Events",
        [
            "All",
            "Line Entry",
            "Line Exit",
            "Entered Zone",
            "Exited Zone",
        ],
    )

    if event_filter != "All":
        df = df[df["Event"] == event_filter]

    # Icons only for display
    df["Event"] = df["Event"].apply(
        lambda x: f"{EVENT_ICONS.get(x, '⚪')} {x}"
    )

    df = df[
        [
            "Time",
            "Event",
            "Track ID",
            "Source",
        ]
    ]

    export_df = export_df[
        [
            "Time",
            "Event",
            "Track ID",
            "Source",
        ]
    ]

    # Export all events
    csv = export_df.to_csv(index=False)

    st.download_button(
        label="📥 Export Events",
        data=csv,
        file_name="events.csv",
        mime="text/csv",
    )

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )