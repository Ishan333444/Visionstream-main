import cv2


class Overlay:

    @staticmethod
    def draw(
        frame,
        fps,
        people_count,
        line_data,
        intrusion_data,
        dwell_data,
        line_counter,
        intrusion_detector,
    ):

        Overlay.draw_feet(frame, line_data["feet"])

        Overlay.draw_fps(frame, fps)

        Overlay.draw_people(frame, people_count)

        Overlay.draw_line_counter(
            frame,
            line_data["entries"],
            line_data["exits"]
        )

        Overlay.draw_intrusion(
            frame,
            intrusion_data["inside"]
        )

        Overlay.draw_dwell_time(
            frame,
            dwell_data
        )

        Overlay.draw_counting_line(
            frame,
            line_counter.start,
            line_counter.end
        )

        Overlay.draw_polygon(
            frame,
            intrusion_detector.polygon,
            intrusion_data["inside"]
        )

        return frame

    # ----------------------------------
    # FPS
    # ----------------------------------

    @staticmethod
    def draw_fps(frame, fps):

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    # ----------------------------------
    # People Count
    # ----------------------------------

    @staticmethod
    def draw_people(frame, people_count):

        cv2.putText(
            frame,
            f"People: {people_count}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 0),
            2
        )

    # ----------------------------------
    # Line Counter
    # ----------------------------------

    @staticmethod
    def draw_line_counter(frame, entries, exits):

        cv2.putText(
            frame,
            f"Entries: {entries}",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Exits: {exits}",
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2
        )

    # ----------------------------------
    # Intrusion Counter
    # ----------------------------------

    @staticmethod
    def draw_intrusion(frame, inside):

        cv2.putText(
            frame,
            f"Inside Zone: {inside}",
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 255),
            2
        )

    # ----------------------------------
    # Feet
    # ----------------------------------

    @staticmethod
    def draw_feet(frame, feet):

        for x, y in feet:

            cv2.circle(
                frame,
                (x, y),
                5,
                (0, 255, 0),
                -1
            )

    # ----------------------------------
    # Counting Line
    # ----------------------------------

    @staticmethod
    def draw_counting_line(frame, start, end):

        cv2.line(
            frame,
            start,
            end,
            (0, 0, 255),
            2
        )

    # ----------------------------------
    # Polygon Zone
    # ----------------------------------

    @staticmethod
    def draw_polygon(frame, polygon, inside):

        color = (0, 255, 0)

        if inside > 0:
            color = (0, 0, 255)

        cv2.polylines(
            frame,
            [polygon],
            True,
            color,
            2
        )

    # ----------------------------------
    # Dwell Timer
    # ----------------------------------

    @staticmethod
    def draw_dwell_time(frame, dwell_data):

        y = 240

        for track_id, dwell in dwell_data.items():

            cv2.putText(
                frame,
                f"ID {track_id}: {dwell:.1f}s",
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            y += 30
