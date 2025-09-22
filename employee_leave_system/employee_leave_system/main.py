from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from db import models
from db import schemas
from email_utils import send_email

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Leave request endpoint
@app.post("/leave/request")
def leave_request(request: schemas.LeaveRequest, db: Session = Depends(get_db)):
    # Store leave request in DB
    leave = models.EmployeeLeave(
        employee_id=request.employee_id,
        from_date=request.from_date,
        to_date=request.to_date,
        reason=request.reason
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)

    # Get employee info
    employee = db.query(models.Employee).filter(models.Employee.id == request.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not employee.parent_id:
        raise HTTPException(status_code=400, detail="Parent/manager not assigned for this employee")

    # Get parent info
    parent = db.query(models.Employee).filter(models.Employee.id == employee.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent/manager not found")

    # Email details for manager (include leave ID)
    subject = f"Leave Request from {employee.name} (Leave ID: {leave.id})"
    body_text = f"""
Hello {parent.name},

Employee {employee.name} has requested leave from {request.from_date} to {request.to_date}.
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
    <p><strong>{employee.name}</strong> has requested leave from <strong>{request.from_date}</strong> 
    to <strong>{request.to_date}</strong>.</p>
    <p><strong>Reason:</strong> {request.reason}</p>
    <p><strong>Leave ID:</strong> {leave.id}</p>
    <p>Please review and approve or reject the request in the system.</p>
    <br>
    <p>Thank you,<br>HR Team</p>
  </body>
</html>
"""

    # Send email to parent
    send_email(parent.email, subject, body_text, body_html)

    return {"message": "Leave request submitted successfully and sent to manager for approval", "leave_id": leave.id}


# Leave approval endpoint
@app.post("/leave/approval")
def leave_approval(request: schemas.LeaveApproval, db: Session = Depends(get_db)):
    # Get leave request
    leave = db.query(models.EmployeeLeave).filter(models.EmployeeLeave.id == request.leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # Update leave status
    leave.status = request.status
    leave.approved_by = request.approved_by
    db.commit()
    db.refresh(leave)

    # Get employee info
    employee = db.query(models.Employee).filter(models.Employee.id == leave.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Get approver info
    approver = db.query(models.Employee).filter(models.Employee.id == request.approved_by).first()

    # Email details for employee
    subject = f"Your Leave Request (ID: {leave.id}) has been {request.status.capitalize()}"
    body_text = f"""
Hello {employee.name},

Your leave request from {leave.from_date} to {leave.to_date} has been {request.status} 
by {approver.name if approver else 'your manager'}.

Leave ID: {leave.id}

Thank you,
HR Team
"""
    body_html = f"""
<html>
  <body>
    <p>Hello {employee.name},</p>
    <p>Your leave request from <strong>{leave.from_date}</strong> to <strong>{leave.to_date}</strong> 
    has been <strong>{request.status}</strong> by {approver.name if approver else 'your manager'}.</p>
    <p><strong>Leave ID:</strong> {leave.id}</p>
    <br>
    <p>Thank you,<br>HR Team</p>
  </body>
</html>
"""

    # Send email to employee
    send_email(employee.email, subject, body_text, body_html)

    return {"message": f"Leave request {request.status} successfully"}
