from pydantic import BaseModel
from typing import Optional


class Alert(BaseModel):
    alert_type: str          # "Critical Task" | "Overdue Task" | "Block Overrun"
    section_id: str
    reference_id: str        # task_id or block_id, whichever triggered it
    severity: Optional[str] = None
    message: str
    risk_score: Optional[float] = None