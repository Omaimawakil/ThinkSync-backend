"""
routes/reports.py
Weekly and monthly report endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query, Depends

from app.database import db
from app.auth.dependencies import get_current_user
from app.schemas.report import WeeklyReport, MonthlyReport
from app.services.report_service import ReportService
from app.exceptions import BadRequestError
from app.utils.validators import ensure_section_exists

logger = logging.getLogger(__name__)
router = APIRouter()


def _who(user: dict) -> str:
    return user.get("username") or user.get("user_id") or "unknown"


@router.get("/reports/weekly", response_model=WeeklyReport)
async def weekly_report(
    section_id: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None, description="ISO format, default: 7 days ago"),
    end_date: Optional[str] = Query(default=None, description="ISO format, default: now"),
    current_user: dict = Depends(get_current_user),
):
    try:
        end = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        start = datetime.fromisoformat(start_date) if start_date else end - timedelta(days=7)
    except ValueError:
        raise BadRequestError("Dates must be ISO format (YYYY-MM-DDTHH:MM:SS)")

    if start > end:
        raise BadRequestError("start_date must be before end_date")

    await ensure_section_exists(db, section_id)

    # Unexpected failures propagate to the global 500 handler, which logs the full traceback.
    report = await ReportService(db).generate_weekly_report(section_id, start, end)
    logger.info("Weekly report generated (section=%s) by %s", section_id, _who(current_user))
    return report


@router.get("/reports/monthly", response_model=MonthlyReport)
async def monthly_report(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    section_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    await ensure_section_exists(db, section_id)

    report = await ReportService(db).generate_monthly_report(section_id, year, month)
    logger.info("Monthly report generated (section=%s, %d-%02d) by %s",
                section_id, year, month, _who(current_user))
    return report