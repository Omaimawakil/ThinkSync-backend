# app/routes/blocks.py
from fastapi import APIRouter, Query, Depends
from app.services import data_service
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/blocks")
async def read_blocks(
    section_id: str = Query(None),
    block_type: str = Query(None),
    overrun_flag: bool = Query(None),
    block_outcome: str = Query(None),
    current_user: dict = Depends(get_current_user),
):
    return await data_service.get_blocks(
        section_id=section_id,
        block_type=block_type,
        overrun_flag=overrun_flag,
        block_outcome=block_outcome,
    )