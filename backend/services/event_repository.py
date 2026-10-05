from datetime import datetime

from backend.services.database import get_connection


def log_event(event_type, track_id, source):
    """
    Stores a new event in the database.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO events
        (
            event_type,
            track_id,
            source,
            timestamp
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            event_type,
            track_id,
            source,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    connection.commit()
    connection.close()


def get_events(limit=None, event_type=None):
    """
    Returns events.
    If limit is None, returns all events.
    Optionally filters by event type.
    """

    connection = get_connection()
    cursor = connection.cursor()

    if event_type:

        if limit is None:

            cursor.execute(
                """
                SELECT *
                FROM events
                WHERE event_type = ?
                ORDER BY id DESC
                """,
                (event_type,),
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM events
                WHERE event_type = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (event_type, limit),
            )

    else:

        if limit is None:

            cursor.execute(
                """
                SELECT *
                FROM events
                ORDER BY id DESC
                """
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )

    rows = cursor.fetchall()

    connection.close()

    events = []

    for row in rows:

        events.append(
            {
                "id": row["id"],
                "event_type": row["event_type"],
                "track_id": row["track_id"],
                "source": row["source"],
                "timestamp": row["timestamp"],
            }
        )

    return events


def get_total_events():
    """
    Returns the total number of logged events.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM events
        """
    )

    total = cursor.fetchone()["total"]

    connection.close()

    return total
