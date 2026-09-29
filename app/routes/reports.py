"""
routes/reports.py
Weekly and monthly report endpoints.
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.database import db
from app.auth.dependencies import get_current_user
from app.schemas.report import WeeklyReport, MonthlyReport
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)
router = APIRouter()


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
        raise HTTPException(status_code=400, detail="Dates must be ISO format (YYYY-MM-DDTHH:MM:SS)")

    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    if section_id:
        section = await db.sections.find_one({"section_id": section_id})
        if not section:
            raise HTTPException(status_code=404, detail=f"Section '{section_id}' not found")

    try:
        service = ReportService(db)
        report = await service.generate_weekly_report(section_id, start, end)
        logger.info(f"Weekly report generated (section={section_id}) by {current_user.get('username')}")
        return report
    except Exception as e:
        logger.error(f"Weekly report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate weekly report")


@router.get("/reports/monthly", response_model=MonthlyReport)
async def monthly_report(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    section_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    if section_id:
        section = await db.sections.find_one({"section_id": section_id})
        if not section:
            raise HTTPException(status_code=404, detail=f"Section '{section_id}' not found")

    try:
        service = ReportService(db)
        report = await service.generate_monthly_report(section_id, year, month)
        logger.info(f"Monthly report generated (section={section_id}, {year}-{month:02d}) by {current_user.get('username')}")
        return report
    except Exception as e:
        logger.error(f"Monthly report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate monthly report")