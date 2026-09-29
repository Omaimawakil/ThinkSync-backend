"""
schemas/report.py
Report response schemas — matches actual ThinkSync collections:
maintenance_tasks, resources, block_history, train_movements.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class OverdueTask(BaseModel):
    task_id: str
    section_id: Optional[str] = None
    severity: Optional[str] = None
    overdue_hours: Optional[int] = None


class TaskMetrics(BaseModel):
    total_open: int
    total_in_progress: int
    total_completed: int
    by_severity: Dict[str, int]
    overdue_count: int
    avg_risk_score: Optional[float] = None
    critical_overdue: List[OverdueTask] = []


class ResourceMetrics(BaseModel):
    total: int
    by_status: Dict[str, int]
    readiness_pct: Optional[float] = None


class BlockMetrics(BaseModel):
    total_blocks: int
    overrun_count: int
    avg_actual_duration_min: Optional[float] = None
    total_overrun_min: int


class TrafficMetrics(BaseModel):
    total_movements: int
    by_category: Dict[str, int]
    avg_delay_minutes: Optional[float] = None


class WeeklyReport(BaseModel):
    report_type: str = "weekly"
    section_id: Optional[str] = None
    start_date: datetime
    end_date: datetime
    generated_at: datetime

    tasks: TaskMetrics
    resources: ResourceMetrics
    blocks: BlockMetrics
    traffic: TrafficMetrics

    efficiency_score: float = Field(ge=0, le=100)


class MonthlyReport(BaseModel):
    report_type: str = "monthly"
    section_id: Optional[str] = None
    year: int
    month: int
    generated_at: datetime

    tasks: TaskMetrics
    resources: ResourceMetrics
    blocks: BlockMetrics
    traffic: TrafficMetrics

    efficiency_score: float = Field(ge=0, le=100)