from fastapi import APIRouter, Query, Depends
from typing import Optional, List
from app.database import db
from app.services.data_service import get_alerts
from app.schemas.alert import Alert
from app.auth.dependencies import get_current_user
from app.utils.validators import ensure_section_exists

router = APIRouter()


@router.get("/alerts", response_model=List[Alert])
async def alerts(
    section_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    await ensure_section_exists(db, section_id)
    return await get_alerts(db, section_id)