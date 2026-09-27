# app/schemas/task.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Geo(BaseModel):
    state: Optional[str] = None
    division: Optional[str] = None
    zone: Optional[str] = None
    district_corridor: Optional[str] = None
    origin_station: Optional[str] = None
    destination_station: Optional[str] = None


class Asset(BaseModel):
    type: Optional[str] = None
    defect_type: Optional[str] = None
    age_years: Optional[int] = None


class Context(BaseModel):
    traffic_density: Optional[int] = None
    previous_failures_12m: Optional[int] = None
    days_since_service: Optional[int] = None
    rail_wear_mm: Optional[float] = None
    track_vibration: Optional[float] = None
    ballast_condition: Optional[str] = None


class Schedule(BaseModel):
    due_date: Optional[datetime] = None
    overdue_hours: Optional[int] = None
    is_overdue: Optional[bool] = None


class Readiness(BaseModel):
    crew_available: Optional[int] = None
    required_crew: Optional[int] = None
    crew_gap: Optional[int] = None
    material_available: Optional[bool] = None
    machine_available: Optional[bool] = None
    power_block_required: Optional[bool] = None
    disconnection_required: Optional[bool] = None
    tower_wagon_required: Optional[bool] = None
    tower_wagon_available: Optional[bool] = None
    readiness_score: Optional[float] = None


class Labels(BaseModel):
    risk_score: Optional[float] = None
    severity: Optional[str] = None
    maintenance_required: Optional[bool] = None
    actual_repair_min: Optional[int] = None


class Task(BaseModel):
    task_id: str
    source_system: Optional[str] = None
    department: Optional[str] = None
    dataset: Optional[str] = None
    section_id: Optional[str] = None
    geo: Optional[Geo] = None
    event_datetime: Optional[datetime] = None
    season: Optional[str] = None
    asset: Optional[Asset] = None
    context: Optional[Context] = None
    schedule: Optional[Schedule] = None
    readiness: Optional[Readiness] = None
    labels: Optional[Labels] = None
class TaskStatusUpdate(BaseModel):
    status: str   # e.g. "In Progress", "Completed", "Cancelled"