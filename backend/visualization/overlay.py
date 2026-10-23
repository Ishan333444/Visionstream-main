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

        Overlay.draw_counting_lines(frame, line_counter.lines)

        Overlay.draw_polygons(frame, intrusion_detector.polygons)

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
    # Counting Lines
    # ----------------------------------

    @staticmethod
    def draw_counting_lines(frame, lines):
        palette = [(0, 0, 255), (255, 120, 0), (0, 200, 255), (255, 0, 200), (0, 200, 0)]
        for index, line in enumerate(lines):
            color = palette[index % len(palette)]
            start, end = tuple(line["start"]), tuple(line["end"])
            cv2.line(frame, start, end, color, 2)
            label = f"{line['name']} E:{line['entries']} X:{line['exits']}"
            cv2.putText(
                frame, label, (max(5, start[0]), max(18, start[1] - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
            )

    # ----------------------------------
    # Intrusion Zones
    # ----------------------------------

    @staticmethod
    def draw_polygons(frame, zones):
        palette = [(0, 255, 0), (255, 0, 255), (0, 255, 255), (255, 150, 0), (150, 255, 0)]
        for index, zone in enumerate(zones):
            color = (0, 0, 255) if zone["inside"] > 0 else palette[index % len(palette)]
            polygon = zone["polygon"]
            cv2.polylines(frame, [polygon], True, color, 2)
            if len(polygon):
                x, y = polygon[0]
                cv2.putText(
                    frame, f"{zone['name']}: {zone['inside']}",
                    (int(x), max(18, int(y) - 8)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, color, 2
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
