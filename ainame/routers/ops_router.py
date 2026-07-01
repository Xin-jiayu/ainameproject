from fastapi import APIRouter

from core.observability import get_metrics_snapshot


router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/metrics")
async def get_metrics():
    return get_metrics_snapshot()
