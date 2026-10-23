import requests
import streamlit as st

from services.api_client import get_device, set_device

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.title("⚙️ Settings")
st.caption("Configure VisionStream inference without editing Python files.")

st.subheader("Compute device")
st.write(
    "Choose where YOLO inference should run. Device availability depends on your "
    "installed PyTorch build and hardware drivers. Changes are applied at a frame "
    "boundary; the model and tracker are reinitialized safely. Tracking-dependent "
    "per-person state is reset, while cumulative line entry/exit totals are retained."
)

try:
    status = get_device()
    current_setting = status.get("setting", "auto")
    label = status.get("label", "Unknown")
    st.metric("Active processor", label)
    preferred_setting = status.get("preferred_setting", current_setting)
    st.caption(
        f"Active mode: `{current_setting}` · Saved preference: `{preferred_setting}` "
        f"· Status: `{status.get('status', 'unknown')}`"
    )
    if status.get("pending_setting"):
        st.info(f"Change to `{status['pending_setting']}` is waiting to be applied.")
    if status.get("error"):
        st.error(f"Last device change failed: {status['error']}")
except requests.RequestException as exc:
    status = None
    current_setting = "auto"
    st.warning(f"Cannot read device status from the VisionStream backend: {exc}")

options = {
    "Automatic (GPU if supported, otherwise CPU)": "auto",
    "CPU": "cpu",
    "NVIDIA GPU (CUDA)": "cuda",
}
labels = list(options.keys())
current_label = next((name for name, value in options.items() if value == current_setting), labels[0])
selected_label = st.selectbox(
    "Run inference on",
    labels,
    index=labels.index(current_label),
    help="CUDA requires a compatible NVIDIA GPU and CUDA-enabled PyTorch. Auto falls back to CPU when no supported GPU is available.",
)
selected_device = options[selected_label]

if st.button("Apply processor", type="primary", use_container_width=True):
    try:
        result = set_device(selected_device)
        if result.get("status") == "pending":
            st.success(f"Device change to {selected_label} queued. It will apply between frames.")
        elif result.get("status") == "idle":
            st.info("VisionStream is already using that device setting.")
        else:
            st.info(f"Device request accepted. Status: {result.get('status', 'unknown')}")
        st.rerun()
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        st.error(f"Could not apply processor setting: {detail}")
    except requests.RequestException as exc:
        st.error(f"Could not contact VisionStream backend: {exc}")

st.divider()
st.caption(
    "The selected device is saved to `backend/config/device_settings.json` after the "
    "new detector successfully initializes. The source-code default in "
    "`backend/config/settings.py` is used only when no saved preference exists. "
    "If the saved hardware backend is unavailable on startup, VisionStream reports "
    "the problem and falls back to Auto for that run without silently overwriting "
    "your saved preference."
)
