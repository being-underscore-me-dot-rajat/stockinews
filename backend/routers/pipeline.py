from fastapi import APIRouter, BackgroundTasks, HTTPException
from services.pipeline import get_status, run_pipeline

router = APIRouter()


@router.post("/api/pipeline/run")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """Manually trigger the news ingestion pipeline (runs in background)."""
    if get_status()["running"]:
        raise HTTPException(status_code=409, detail="Pipeline is already running")
    background_tasks.add_task(run_pipeline)
    return {"status": "started"}


@router.get("/api/pipeline/status")
def pipeline_status():
    """Return the current pipeline status and last-run statistics."""
    return get_status()
