# app/routes/traffic.py
from fastapi import APIRouter, Query, Depends
from app.database import db
from app.services import data_service
from app.auth.dependencies import get_current_user
from app.utils.validators import ensure_section_exists

router = APIRouter()


@router.get("/traffic")
async def read_traffic(
    section_id: str | None = Query(None),
    direction: str | None = Query(None),
    priority: str | None = Query(None),
    train_category: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    await ensure_section_exists(db, section_id)
    return await data_service.get_traffic(
        section_id=section_id,
        direction=direction,
        priority=priority,
        train_category=train_category,
    )