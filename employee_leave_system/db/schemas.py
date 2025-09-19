from pydantic import BaseModel
from datetime import date
from typing import Optional

class LeaveRequest(BaseModel):
    employee_id: int
    from_date: date
    to_date: date
    reason: Optional[str]

class LeaveApproval(BaseModel):
    leave_id: int
    approved_by: int
    status: str 