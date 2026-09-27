# app/routes/tasks.py
from fastapi import APIRouter, Query, Depends
from app.services import data_service
from fastapi import HTTPException
from app.schemas.task import TaskStatusUpdate
from app.services.data_service import update_task_status
from app.database import db
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter()

@router.patch("/tasks/{task_id}/status")
async def patch_task_status(
    task_id: str,
    body: TaskStatusUpdate,
    current_user: dict = Depends(require_roles("Engineering/S&T/TRD", "Admin")),
):
    matched, modified = await update_task_status(db, task_id, body.status)
    if matched == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "new_status": body.status, "modified": modified > 0}

@router.get("/tasks")
async def read_tasks(
    section_id: str = Query(None),
    department: str = Query(None),
    severity: str = Query(None),
    is_overdue: bool = Query(None),
    current_user: dict = Depends(get_current_user),
):
    return await data_service.get_tasks(
        section_id=section_id,
        department=department,
        severity=severity,
        is_overdue=is_overdue,
    )