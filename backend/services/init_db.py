from backend.services.database import get_connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # -------------------------
    # Analytics
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (

            id INTEGER PRIMARY KEY,

            people INTEGER,

            entries INTEGER,

            exits INTEGER,

            inside_zone INTEGER,

            density TEXT,

            object_counts TEXT,

            updated_at TEXT

        )
    """)

    # -------------------------
    # Events
    # -------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        track_id INTEGER,
        source TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    # -------------------------
    # Create first analytics row
    # -------------------------

    cursor.execute("""
        INSERT OR IGNORE INTO analytics
        (
            id,
            people,
            entries,
            exits,
            inside_zone,
            density,
            object_counts,
            updated_at
        )
        VALUES
        (
            1,
            0,
            0,
            0,
            0,
            'Low',
            '{}',
            ''
        )
    """)

    connection.commit()

    connection.close()


if __name__ == "__main__":

    initialize_database()

    print("Database initialized.")
