# app/routes/resources.py
from fastapi import APIRouter, Query, Depends
from app.database import db
from app.services import data_service
from app.auth.dependencies import get_current_user
from app.utils.validators import ensure_section_exists

router = APIRouter()


@router.get("/resources")
async def read_resources(
    section_id: str | None = Query(None),
    resource_type: str | None = Query(None),
    status: str | None = Query(None),
    department: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    await ensure_section_exists(db, section_id)
    return await data_service.get_resources(
        section_id=section_id,
        resource_type=resource_type,
        status=status,
        department=department,
    )