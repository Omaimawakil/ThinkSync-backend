# app/routes/blocks.py
from fastapi import APIRouter, Query, Depends
from app.database import db
from app.services import data_service
from app.auth.dependencies import get_current_user
from app.utils.validators import ensure_section_exists

router = APIRouter()


@router.get("/blocks")
async def read_blocks(
    section_id: str | None = Query(None),
    block_type: str | None = Query(None),
    overrun_flag: bool | None = Query(None),
    block_outcome: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    await ensure_section_exists(db, section_id)
    return await data_service.get_blocks(
        section_id=section_id,
        block_type=block_type,
        overrun_flag=overrun_flag,
        block_outcome=block_outcome,
    )