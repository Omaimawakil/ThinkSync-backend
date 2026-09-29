# app/routes/tasks.py
import logging

from fastapi import APIRouter, Query, Depends

from app.database import db
from app.services import data_service
from app.services.data_service import update_task_status
from app.schemas.task import TaskStatusUpdate
from app.auth.dependencies import get_current_user, require_roles
from app.exceptions import NotFoundError
from app.utils.validators import ensure_section_exists

logger = logging.getLogger(__name__)
router = APIRouter()


@router.patch("/tasks/{task_id}/status")
async def patch_task_status(
    task_id: str,
    body: TaskStatusUpdate,
    current_user: dict = Depends(require_roles("Engineering/S&T/TRD", "Admin")),
):
    matched, modified = await update_task_status(db, task_id, body.status)
    if matched == 0:
        raise NotFoundError("Task", task_id)

    logger.info(
        "Task '%s' status set to '%s' by %s (modified=%s)",
        task_id, body.status, current_user.get("user_id"), modified > 0,
    )
    return {"task_id": task_id, "new_status": body.status, "modified": modified > 0}


@router.get("/tasks")
async def read_tasks(
    section_id: str | None = Query(None),
    department: str | None = Query(None),
    severity: str | None = Query(None),
    is_overdue: bool | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    await ensure_section_exists(db, section_id)
    return await data_service.get_tasks(
        section_id=section_id,
        department=department,
        severity=severity,
        is_overdue=is_overdue,
    )