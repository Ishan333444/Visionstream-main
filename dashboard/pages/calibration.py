"""Streamlit calibration editor for multiple counting lines and intrusion zones."""
import copy
import uuid

import cv2
import numpy as np
import requests
import streamlit as st

from services.api_client import get_calibration, set_calibration, get_snapshot

st.set_page_config(page_title="Calibration", page_icon="📐", layout="wide")
st.title("📐 Camera Calibration")
st.caption(
    "Configure as many counting lines and intrusion zones as you need. Coordinates "
    "are normalized to the camera frame, so they remain aligned if the frame resolution changes."
)


def _new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _load_initial():
    try:
        response = get_calibration()
        calibration = response.get("calibration", response)
        st.session_state["cal_lines"] = copy.deepcopy(calibration.get("lines", []))
        st.session_state["cal_zones"] = copy.deepcopy(calibration.get("zones", []))
        st.session_state["cal_status"] = response.get("status", "loaded")
        st.session_state["cal_error"] = response.get("error")
    except requests.RequestException as exc:
        st.error(f"Could not load calibration from the backend: {exc}")
        st.stop()


if "cal_lines" not in st.session_state or "cal_zones" not in st.session_state:
    _load_initial()

# Refresh backend status on every page rerun without overwriting unsaved widget edits.
try:
    calibration_status = get_calibration()
    status_value = calibration_status.get("status", "unknown")
    if calibration_status.get("pending") or status_value in {"pending", "applying"}:
        st.info("A calibration change is waiting to be applied at the next frame boundary.")
    elif status_value == "failed":
        st.error(f"The last calibration change failed: {calibration_status.get('error') or 'Unknown error'}")
    elif status_value == "applied":
        st.success("The active calibration is up to date.")
except requests.RequestException:
    pass


def _read_lines_from_widgets():
    lines = []
    for index, line in enumerate(st.session_state.get("cal_lines", []), 1):
        line_id = line["id"]
        lines.append({
            "id": line_id,
            "name": st.session_state.get(f"line_{line_id}_name", line.get("name", f"Counting line {index}")),
            "start": [
                float(st.session_state.get(f"line_{line_id}_sx", line["start"][0])),
                float(st.session_state.get(f"line_{line_id}_sy", line["start"][1])),
            ],
            "end": [
                float(st.session_state.get(f"line_{line_id}_ex", line["end"][0])),
                float(st.session_state.get(f"line_{line_id}_ey", line["end"][1])),
            ],
        })
    return lines


def _read_zones_from_widgets():
    zones = []
    for index, zone in enumerate(st.session_state.get("cal_zones", []), 1):
        zone_id = zone["id"]
        points = []
        for point_index, point in enumerate(zone["points"]):
            points.append([
                float(st.session_state.get(f"zone_{zone_id}_p{point_index}_x", point[0])),
                float(st.session_state.get(f"zone_{zone_id}_p{point_index}_y", point[1])),
            ])
        zones.append({
            "id": zone_id,
            "name": st.session_state.get(f"zone_{zone_id}_name", zone.get("name", f"Intrusion zone {index}")),
            "points": points,
        })
    return zones


st.subheader("Counting lines")
st.caption(
    "Each line independently counts crossings in both directions. Direction is based on the "
    "orientation of its endpoints: left-to-right is entry, right-to-left is exit."
)
for index, line in enumerate(st.session_state["cal_lines"], 1):
    line_id = line["id"]
    with st.expander(f"Line {index}: {line.get('name', line_id)}", expanded=True):
        cols = st.columns([2, 1, 1, 1, 1, 0.8])
        cols[0].text_input("Name", value=line.get("name", f"Counting line {index}"), key=f"line_{line_id}_name")
        cols[1].number_input("Start X", 0.0, 1.0, float(line["start"][0]), step=0.01, format="%.3f", key=f"line_{line_id}_sx")
        cols[2].number_input("Start Y", 0.0, 1.0, float(line["start"][1]), step=0.01, format="%.3f", key=f"line_{line_id}_sy")
        cols[3].number_input("End X", 0.0, 1.0, float(line["end"][0]), step=0.01, format="%.3f", key=f"line_{line_id}_ex")
        cols[4].number_input("End Y", 0.0, 1.0, float(line["end"][1]), step=0.01, format="%.3f", key=f"line_{line_id}_ey")
        if cols[5].button("Remove", key=f"remove_line_{line_id}", disabled=len(st.session_state["cal_lines"]) <= 1):
            st.session_state["cal_lines"] = [item for item in _read_lines_from_widgets() if item["id"] != line_id]
            st.rerun()

if st.button("＋ Add counting line", key="add_counting_line"):
    st.session_state["cal_lines"] = _read_lines_from_widgets() + [{
        "id": _new_id("line"), "name": f"Counting line {len(st.session_state['cal_lines']) + 1}",
        "start": [0.25, 0.5], "end": [0.75, 0.5],
    }]
    st.rerun()

st.divider()
st.subheader("Intrusion zones")
st.caption("Each zone is a polygon with at least three points. A person inside overlapping zones counts once in overall occupancy.")
for index, zone in enumerate(st.session_state["cal_zones"], 1):
    zone_id = zone["id"]
    with st.expander(f"Zone {index}: {zone.get('name', zone_id)}", expanded=True):
        st.text_input("Zone name", value=zone.get("name", f"Intrusion zone {index}"), key=f"zone_{zone_id}_name")
        for point_index, point in enumerate(zone["points"]):
            cols = st.columns([1, 1, 0.5])
            cols[0].number_input(f"Point {point_index + 1} X", 0.0, 1.0, float(point[0]), step=0.01, format="%.3f", key=f"zone_{zone_id}_p{point_index}_x")
            cols[1].number_input(f"Point {point_index + 1} Y", 0.0, 1.0, float(point[1]), step=0.01, format="%.3f", key=f"zone_{zone_id}_p{point_index}_y")
            if cols[2].button("Remove point", key=f"remove_point_{zone_id}_{point_index}", disabled=len(zone["points"]) <= 3):
                zones = _read_zones_from_widgets()
                for item in zones:
                    if item["id"] == zone_id:
                        item["points"].pop(point_index)
                # Point indexes shift after deletion, so clear their widget state
                # to ensure values remain attached to the intended vertices.
                for key in list(st.session_state.keys()):
                    if key.startswith(f"zone_{zone_id}_p") and (key.endswith("_x") or key.endswith("_y")):
                        del st.session_state[key]
                st.session_state["cal_zones"] = zones
                st.rerun()
        cols = st.columns([1, 1, 1])
        if cols[0].button("＋ Add point", key=f"add_point_{zone_id}"):
            zones = _read_zones_from_widgets()
            for item in zones:
                if item["id"] == zone_id:
                    item["points"].append([0.5, 0.5])
            st.session_state["cal_zones"] = zones
            st.rerun()
        if cols[2].button("Remove zone", key=f"remove_zone_{zone_id}"):
            st.session_state["cal_zones"] = [item for item in _read_zones_from_widgets() if item["id"] != zone_id]
            st.rerun()

if st.button("＋ Add intrusion zone", key="add_intrusion_zone"):
    st.session_state["cal_zones"] = _read_zones_from_widgets() + [{
        "id": _new_id("zone"), "name": f"Intrusion zone {len(st.session_state['cal_zones']) + 1}",
        "points": [[0.35, 0.35], [0.65, 0.35], [0.65, 0.65], [0.35, 0.65]],
    }]
    st.rerun()

st.divider()
st.subheader("Preview")
st.caption("The preview overlays your current unsaved geometry on the latest frame received by the backend.")
try:
    snapshot_bytes = get_snapshot()
    frame = cv2.imdecode(np.frombuffer(snapshot_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is not None:
        height, width = frame.shape[:2]
        for index, line in enumerate(_read_lines_from_widgets()):
            start = (int(line["start"][0] * width), int(line["start"][1] * height))
            end = (int(line["end"][0] * width), int(line["end"][1] * height))
            color = [(0, 0, 255), (255, 120, 0), (0, 200, 255), (255, 0, 200)][index % 4]
            cv2.line(frame, start, end, color, 3)
            cv2.putText(frame, line["name"], (start[0], max(20, start[1] - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        for index, zone in enumerate(_read_zones_from_widgets()):
            points = np.array([[int(x * width), int(y * height)] for x, y in zone["points"]], dtype=np.int32)
            color = [(0, 255, 0), (255, 0, 255), (0, 255, 255), (255, 150, 0)][index % 4]
            cv2.polylines(frame, [points], True, color, 3)
            if len(points):
                cv2.putText(frame, zone["name"], tuple(points[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), caption=f"Camera preview ({width} × {height})", use_container_width=True)
    else:
        st.warning("The backend has not supplied a usable camera frame yet.")
except requests.RequestException as exc:
    st.warning(f"Live preview unavailable: {exc}. You can still edit normalized coordinates below.")

if st.button("Save and apply calibration", type="primary", use_container_width=True):
    calibration = {"lines": _read_lines_from_widgets(), "zones": _read_zones_from_widgets()}
    try:
        result = set_calibration(calibration)
        st.session_state["cal_status"] = result.get("status", "pending")
        st.session_state["cal_error"] = result.get("error")
        if result.get("status") == "pending":
            st.success("Calibration accepted. It will be applied at the next frame boundary and saved to disk.")
        elif result.get("status") == "saved_for_next_start":
            st.success("Calibration saved; it will load when the engine starts.")
        else:
            st.success(f"Calibration status: {result.get('status', 'saved')}")
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        st.error(f"Calibration was rejected: {detail}")
    except requests.RequestException as exc:
        st.error(f"Could not contact VisionStream backend: {exc}")

if st.session_state.get("cal_error"):
    st.error(st.session_state["cal_error"])

st.caption("Changes take effect without restarting VisionStream. Crossing-state history and dwell timers reset when calibration changes; cumulative line totals are preserved where possible.")
