import json
from datetime import datetime

from backend.services.database import get_connection


def update_latest(
    people,
    entries,
    exits,
    inside_zone,
    density,
    object_counts,
):
    """
    Updates the latest analytics row (id = 1).
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE analytics
        SET
            people = ?,
            entries = ?,
            exits = ?,
            inside_zone = ?,
            density = ?,
            object_counts = ?,
            updated_at = ?
        WHERE id = 1
        """,
        (
            people,
            entries,
            exits,
            inside_zone,
            density,
            json.dumps(object_counts),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    connection.commit()
    connection.close()


def get_latest():
    """
    Returns the latest analytics as a Python dictionary.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM analytics
        WHERE id = 1
        """
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return {
        "people": row["people"],
        "entries": row["entries"],
        "exits": row["exits"],
        "inside_zone": row["inside_zone"],
        "density": row["density"],
        "object_counts": json.loads(row["object_counts"]),
        "updated_at": row["updated_at"],
    }
