from threading import Thread

from fastapi import FastAPI

from backend.engine.vision_engine import VisionEngine

from backend.api.health import router as health_router
from backend.api.analytics import router as analytics_router
from backend.api.events import router as events_router
from backend.api.stats import router as stats_router
from backend.api.video import router as video_router
from backend.services.init_db import initialize_database


app = FastAPI(
    title="VisionStream API",
    version="1.0.0",
    description="Real-Time Computer Vision Analytics"
)

engine = None


def run_engine():
    global engine

    try:
        engine = VisionEngine()
        app.state.engine_status = "running"
        print("VisionStream engine status: running")

        engine.run()

        app.state.engine_status = "stopped"
        print("VisionStream engine status: stopped")

    except Exception as e:
        app.state.engine_status = "failed"
        print(f"VisionStream engine failed: {e}")
        raise


@app.on_event("startup")
def startup_event():
    initialize_database()

    app.state.engine_status = "starting"

    thread = Thread(
        target=run_engine,
        daemon=True,
    )

    thread.start()


@app.get("/")
def root():
    return {
        "message": "VisionStream API is running!"
    }


app.include_router(health_router)
app.include_router(analytics_router)
app.include_router(events_router)
app.include_router(stats_router)
app.include_router(video_router)