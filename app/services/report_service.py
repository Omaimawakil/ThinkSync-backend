"""
services/report_service.py
Aggregates maintenance_tasks, resources, block_history, train_movements
into weekly/monthly reports. Field names match the real schemas
(task.py, resource.py, block.py, traffic.py) and the query patterns
already used and tested in services/data_service.py.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict

from app.schemas.report import (
    WeeklyReport,
    MonthlyReport,
    TaskMetrics,
    ResourceMetrics,
    BlockMetrics,
    TrafficMetrics,
    OverdueTask,
)


async def _get_task_metrics(
    db, section_id: Optional[str], start: datetime, end: datetime
) -> TaskMetrics:
    match_stage = {"event_datetime": {"$gte": start, "$lte": end}}
    if section_id:
        match_stage["section_id"] = section_id

    docs = await db.maintenance_tasks.find(match_stage).to_list(length=None)

    total_open = 0
    total_in_progress = 0
    total_completed = 0
    by_severity: Dict[str, int] = {}
    overdue_count = 0
    risk_scores = []
    critical_overdue = []

    for doc in docs:
        # task_status is missing on most existing docs; default to "Open"
        status = doc.get("task_status") or "Open"
        if status == "Completed":
            total_completed += 1
        elif status == "In Progress":
            total_in_progress += 1
        else:
            total_open += 1

        labels = doc.get("labels") or {}
        severity = labels.get("severity")
        if severity:
            by_severity[severity] = by_severity.get(severity, 0) + 1

        risk_score = labels.get("risk_score")
        if risk_score is not None:
            risk_scores.append(risk_score)

        schedule = doc.get("schedule") or {}
        if schedule.get("is_overdue"):
            overdue_count += 1
            if severity in ("High", "Critical") and len(critical_overdue) < 5:
                critical_overdue.append(
                    OverdueTask(
                        task_id=doc.get("task_id", ""),
                        section_id=doc.get("section_id"),
                        severity=severity,
                        overdue_hours=schedule.get("overdue_hours"),
                    )
                )

    avg_risk = round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else None

    return TaskMetrics(
        total_open=total_open,
        total_in_progress=total_in_progress,
        total_completed=total_completed,
        by_severity=by_severity,
        overdue_count=overdue_count,
        avg_risk_score=avg_risk,
        critical_overdue=critical_overdue,
    )


async def _get_resource_metrics(db, section_id: Optional[str]) -> ResourceMetrics:
    # Resources have no timestamp field to filter by period, so this is a
    # current snapshot (same approach as get_resource_kpis in data_service.py)
    match_stage = {}
    if section_id:
        match_stage["section_id"] = section_id

    pipeline = [
        {"$match": match_stage},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    result = await db.resources.aggregate(pipeline).to_list(length=None)
    by_status = {doc["_id"]: doc["count"] for doc in result if doc["_id"]}
    total = sum(by_status.values())
    available = by_status.get("Available", 0)
    readiness_pct = round((available / total) * 100, 1) if total else None

    return ResourceMetrics(total=total, by_status=by_status, readiness_pct=readiness_pct)


async def _get_block_metrics(
    db, section_id: Optional[str], start: datetime, end: datetime
) -> BlockMetrics:
    match_stage = {"block_start": {"$gte": start, "$lte": end}}
    if section_id:
        match_stage["section_id"] = section_id

    docs = await db.block_history.find(match_stage).to_list(length=None)

    total_blocks = len(docs)
    overrun_count = 0
    total_overrun_min = 0
    durations = []

    for doc in docs:
        if doc.get("overrun_flag"):
            overrun_count += 1
        overrun_min = doc.get("overrun_min") or 0
        total_overrun_min += overrun_min
        duration = doc.get("actual_duration_min")
        if duration is not None:
            durations.append(duration)

    avg_duration = round(sum(durations) / len(durations), 1) if durations else None

    return BlockMetrics(
        total_blocks=total_blocks,
        overrun_count=overrun_count,
        avg_actual_duration_min=avg_duration,
        total_overrun_min=total_overrun_min,
    )


async def _get_traffic_metrics(
    db, section_id: Optional[str], start: datetime, end: datetime
) -> TrafficMetrics:
    match_stage = {"scheduled_entry": {"$gte": start, "$lte": end}}
    if section_id:
        match_stage["section_id"] = section_id

    docs = await db.train_movements.find(match_stage).to_list(length=None)

    total_movements = len(docs)
    by_category: Dict[str, int] = {}
    delays = []

    for doc in docs:
        category = doc.get("train_category") or "Unknown"
        by_category[category] = by_category.get(category, 0) + 1
        delay = doc.get("delay_minutes")
        if delay is not None:
            delays.append(delay)

    avg_delay = round(sum(delays) / len(delays), 1) if delays else None

    return TrafficMetrics(
        total_movements=total_movements,
        by_category=by_category,
        avg_delay_minutes=avg_delay,
    )


def _compute_efficiency_score(
    tasks: TaskMetrics, resources: ResourceMetrics, blocks: BlockMetrics
) -> float:
    total_tasks = tasks.total_open + tasks.total_in_progress + tasks.total_completed
    on_time_pct = (tasks.total_completed / total_tasks * 100) if total_tasks else 0

    readiness = resources.readiness_pct or 0

    overrun_penalty = min(blocks.overrun_count * 2, 20)

    score = (on_time_pct * 0.5) + (readiness * 0.3) + ((100 - overrun_penalty) * 0.2)
    return round(min(max(score, 0), 100), 2)


class ReportService:
    def __init__(self, db):
        self.db = db

    async def generate_weekly_report(
        self, section_id: Optional[str], start_date: datetime, end_date: datetime
    ) -> WeeklyReport:
        tasks, resources, blocks, traffic = await asyncio.gather(
            _get_task_metrics(self.db, section_id, start_date, end_date),
            _get_resource_metrics(self.db, section_id),
            _get_block_metrics(self.db, section_id, start_date, end_date),
            _get_traffic_metrics(self.db, section_id, start_date, end_date),
        )

        efficiency_score = _compute_efficiency_score(tasks, resources, blocks)

        return WeeklyReport(
            section_id=section_id,
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.utcnow(),
            tasks=tasks,
            resources=resources,
            blocks=blocks,
            traffic=traffic,
            efficiency_score=efficiency_score,
        )

    async def generate_monthly_report(
        self, section_id: Optional[str], year: int, month: int
    ) -> MonthlyReport:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        tasks, resources, blocks, traffic = await asyncio.gather(
            _get_task_metrics(self.db, section_id, start_date, end_date),
            _get_resource_metrics(self.db, section_id),
            _get_block_metrics(self.db, section_id, start_date, end_date),
            _get_traffic_metrics(self.db, section_id, start_date, end_date),
        )

        efficiency_score = _compute_efficiency_score(tasks, resources, blocks)

        return MonthlyReport(
            section_id=section_id,
            year=year,
            month=month,
            generated_at=datetime.utcnow(),
            tasks=tasks,
            resources=resources,
            blocks=blocks,
            traffic=traffic,
            efficiency_score=efficiency_score,
        )