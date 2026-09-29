from fastapi import APIRouter, Query, Depends
from app.database import db
from app.services.data_service import get_dashboard_summary
from app.schemas.dashboard import DashboardSummary
from app.auth.dependencies import get_current_user
from app.utils.validators import ensure_section_exists

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard(
    section_id: str | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    await ensure_section_exists(db, section_id)
    return await get_dashboard_summary(db, section_id)