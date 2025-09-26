from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List

# -----------------------------
# Request Schemas
# -----------------------------

class LeaveRequest(BaseModel):
    from_date: date
    to_date: date
    reason: Optional[str]

class LeaveApproval(BaseModel):
    leave_id: int
    status: str  # approved / rejected

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# -----------------------------
# Response Schemas
# -----------------------------
class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    from_date: date
    to_date: date
    reason: Optional[str]
    leave_type: Optional[str]
    status: str
    approved_by: Optional[int]
    comments: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# ----------------- EMPLOYEE CRUD SCHEMAS -----------------
class EmployeeBase(BaseModel):
    name: str
    email: str
    position: str | None = None
    parent_id: int | None = None

class EmployeeCreate(EmployeeBase):
    password: str 

class EmployeeUpdate(EmployeeBase):
    password: str | None = None 

class EmployeeRead(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# ----------------- EMPLOYEELEAVE CRUD SCHEMAS -----------------
class EmployeeLeaveBase(BaseModel):
    employee_id: int
    from_date: date
    to_date: date
    reason: str | None = None
    leave_type: str | None = "casual"

class EmployeeLeaveCreate(EmployeeLeaveBase):
    pass

class EmployeeLeaveUpdate(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
    reason: str | None = None
    leave_type: str | None = None
    status: str | None = None
    approved_by: int | None = None
    comments: str | None = None

class EmployeeLeaveRead(EmployeeLeaveBase):
    id: int
    status: str
    approved_by: int | None
    comments: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# ----------------- ATTENDANCE & CALENDAR SCHEMAS -----------------
class AttendanceRead(BaseModel):
    date: date
    status: str

    model_config = {
        "from_attributes": True
    }

class CompanyCalendarRead(BaseModel):
    date: date
    is_holiday: bool
    holiday_name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class CalendarDay(BaseModel):
    date: date
    status: str

class MonthlyCalendarResponse(BaseModel):
    employee_id: int
    month: str
    year: int
    calendar_view: List[CalendarDay]
