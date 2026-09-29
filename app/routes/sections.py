from fastapi import APIRouter, Query, Depends
from app.services.data_service import get_all_sections
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/api/sections")
async def sections(
    division: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    return await get_all_sections(division)