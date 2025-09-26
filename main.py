from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import extract
from typing import List
from db import models, schemas
from utils.email_utils import send_email
from db.database import get_db
from db.crud_endpoints.employee_crud import router as employee_router 
from db.crud_endpoints.employee_leave_crud import router as employee_leave_router 
from core import auth, security
from datetime import datetime, date
import calendar
from dependencies import require_permission

app = FastAPI(title="Employee Leave Management System")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        
    allow_credentials=True,
    allow_methods=["*"],           
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(employee_router, prefix="/crud")
app.include_router(employee_leave_router, prefix="/crud")

# -----------------------------
# Leave request endpoint
# -----------------------------
@app.post("/leave/request", tags=["Leave Management"], summary="Submit leave request")
def leave_request(
    request: schemas.LeaveRequest,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("create_leave"))
):
    leave = models.EmployeeLeave(
        employee_id=current_user.id,
        from_date=request.from_date,
        to_date=request.to_date,
        reason=request.reason
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)

    if not current_user.parent_id:
        raise HTTPException(status_code=400, detail="Parent/senior not assigned")
    parent = db.query(models.Employee).filter(models.Employee.id == current_user.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent/senior not found")

    subject = f"Leave Request from {current_user.name} (Leave ID: {leave.id})"
    body_text = f"""
Hello {parent.name},

Employee {current_user.name} has requested leave from {request.from_date} to {request.to_date}.
Reason: {request.reason}

Leave ID: {leave.id}

Please review and approve or reject the request in the system.

Thank you,
HR Team
"""
    body_html = f"""
<html>
  <body>
    <p>Hello {parent.name},</p>
    <p><strong>{current_user.name}</strong> has requested leave from <strong>{request.from_date}</strong> 
    to <strong>{request.to_date}</strong>.</p>
    <p><strong>Reason:</strong> {request.reason}</p>
    <p><strong>Leave ID:</strong> {leave.id}</p>
    <p>Please review and approve or reject the request in the system.</p>
    <br>
    <p>Thank you,<br>HR Team</p>
  </body>
</html>
"""
    email_sent = send_email(parent.email, subject, body_text, body_html)

    if email_sent:
        return {
            "message": "Leave request submitted successfully and email sent to parent/senior",
            "leave_id": leave.id
        }
    else:
        return {
            "message": "Leave request submitted successfully but failed to send email",
            "leave_id": leave.id
        }

# -----------------------------
# Get leave requests for approval
# -----------------------------
@app.get("/leave/approval", tags=["Leave Management"], summary="View leave requests for approval", response_model=List[schemas.LeaveResponse])
def get_leave_requests(
    status: str = Query("pending", enum=["pending", "approved", "rejected"]),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("approve_leave"))
):
    if current_user.role == "manager":
        # Show only direct reports
        leaves = db.query(models.EmployeeLeave).join(models.Employee)\
            .filter(models.Employee.parent_id == current_user.id,
                    models.EmployeeLeave.status == status)\
            .all()
    elif current_user.role in ["hr", "admin"]:
        # Show all leaves
        leaves = db.query(models.EmployeeLeave).filter(models.EmployeeLeave.status == status).all()
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view leave approvals")
    return leaves

# -----------------------------
# Approve or reject leave request
# -----------------------------
@app.post("/leave/approval", tags=["Leave Management"], summary="Approve or reject leave request")
def leave_approval(
    request: schemas.LeaveApproval,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("approve_leave"))
):
    leave = db.query(models.EmployeeLeave).filter(models.EmployeeLeave.id == request.leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    employee = db.query(models.Employee).filter(models.Employee.id == leave.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Parent approval check
    if current_user.role == "employee" and employee.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to approve this leave request")

    leave.status = request.status
    leave.approved_by = current_user.id
    db.commit()
    db.refresh(leave)

    # Email to employee
    subject = f"Your Leave Request (ID: {leave.id}) has been {request.status.capitalize()}"
    body_text = f"""
Hello {employee.name},

Your leave request from {leave.from_date} to {leave.to_date} has been {request.status} by {current_user.name}.

Leave ID: {leave.id}

Thank you,
HR Team
"""
    body_html = f"""
<html>
  <body>
    <p>Hello {employee.name},</p>
    <p>Your leave request from <strong>{leave.from_date}</strong> to <strong>{leave.to_date}</strong> 
    has been <strong>{request.status}</strong> by {current_user.name}.</p>
    <p><strong>Leave ID:</strong> {leave.id}</p>
    <br>
    <p>Thank you,<br>HR Team</p>
  </body>
</html>
"""
    email_sent = send_email(employee.email, subject, body_text, body_html)

    if email_sent:
        return {
            "message": f"Leave request {request.status} successfully and email sent to employee"
        }
    else:
        return {
            "message": f"Leave request {request.status} successfully but failed to send email"
        }

# -----------------------------
# Cancel leave request
# -----------------------------
@app.put("/leave/cancel/{leave_id}", tags=["Leave Management"], summary="Cancel leave request")
def cancel_leave_request(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("cancel_own_leave"))
):
    leave = db.query(models.EmployeeLeave).filter(models.EmployeeLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # Only employee who requested it can cancel
    if current_user.role == "employee" and leave.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this leave")

    if leave.status not in ["pending"]:  # Only pending leaves can be cancelled
        raise HTTPException(status_code=400, detail="Only pending leaves can be cancelled")

    leave.status = "cancelled"
    db.commit()
    db.refresh(leave)
    return {"message": "Leave request cancelled successfully"}

# -----------------------------
# Monthly Attendance Calendar
# -----------------------------
@app.get(
    "/attendance",
    response_model=schemas.MonthlyCalendarResponse,
    tags=["Attendance"],
    summary="Get monthly attendance calendar"
)
def get_monthly_calendar(
    month: int = Query(default=datetime.now().month, ge=1, le=12),
    year: int = Query(default=datetime.now().year),
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("view_own_attendance"))
):
    employee_id = current_user.id

    #Prepare all days of the month
    days_in_month = calendar.monthrange(year, month)[1]
    calendar_days = {day: {"status": "Not Marked"} for day in range(1, days_in_month + 1)}

    # Fetch attendance records for the employee
    records = (
        db.query(models.Attendance)
        .filter(
            models.Attendance.employee_id == employee_id,
            extract("month", models.Attendance.date) == month,
            extract("year", models.Attendance.date) == year
        )
        .all()
    )
    for r in records:
        calendar_days[r.date.day]["status"] = r.status

    # Fetch company holidays
    holidays = (
        db.query(models.CompanyCalendar)
        .filter(
            extract("month", models.CompanyCalendar.date) == month,
            extract("year", models.CompanyCalendar.date) == year,
            models.CompanyCalendar.is_holiday == True
        )
        .all()
    )
    for h in holidays:
        day = h.date.day
        if calendar_days[day]["status"] == "Not Marked":
            calendar_days[day]["status"] = f"Holiday ({h.holiday_name or 'Holiday'})"

    # Build final calendar response
    calendar_view = [
        {"date": date(year, month, day).isoformat(), "status": info["status"]}
        for day, info in calendar_days.items()
    ]

    return {
        "employee_id": employee_id,
        "month": calendar.month_name[month],
        "year": year,
        "calendar_view": calendar_view
    }
