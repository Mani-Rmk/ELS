from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.schemas import EmployeeLeaveCreate, EmployeeLeaveRead, EmployeeLeaveUpdate
from db.models import EmployeeLeave, Employee
from db.database import get_db
from dependencies import require_permission
from core import security

# ----------------- ROUTER -----------------
router = APIRouter(prefix="/leaves", tags=["Employee Leaves"])

# -------- REQUEST LEAVE --------
@router.post("/", response_model=EmployeeLeaveRead)
def request_leave(
    leave: EmployeeLeaveCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("create_leave"))
):
    db_leave = EmployeeLeave(
        employee_id=current_user.id,
        from_date=leave.from_date,
        to_date=leave.to_date,
        reason=leave.reason
    )
    db.add(db_leave)
    try:
        db.commit()
        db.refresh(db_leave)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating leave: {e}")
    return db_leave

# -------- GET ALL LEAVES --------
@router.get("/", response_model=List[EmployeeLeaveRead])
def get_leaves(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("view_leave"))
):
    if current_user.role == "admin" or current_user.role == "hr":
        # HR/Admin sees all leaves
        return db.query(EmployeeLeave).all()
    elif current_user.role == "manager":
        # Manager sees leaves of direct reports
        return db.query(EmployeeLeave).join(Employee)\
            .filter(Employee.parent_id == current_user.id).all()
    else:
        # Employee sees own leaves
        return db.query(EmployeeLeave).filter(EmployeeLeave.employee_id == current_user.id).all()

# -------- GET SINGLE LEAVE --------
@router.get("/{leave_id}", response_model=EmployeeLeaveRead)
def get_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("view_leave"))
):
    leave = db.query(EmployeeLeave).filter(EmployeeLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    # Employee can view only own leaves
    # Manager can view only direct reports
    if current_user.role == "manager":
        employee = db.query(Employee).filter(Employee.id == leave.employee_id).first()
        if employee.parent_id != current_user.id:
            raise HTTPException(status_code=403, detail="You cannot view this leave")
    elif current_user.role not in ["admin", "hr"] and leave.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot view this leave")

    return leave

# -------- UPDATE LEAVE --------
@router.put("/{leave_id}", response_model=EmployeeLeaveRead)
def update_leave(
    leave_id: int,
    updated: EmployeeLeaveUpdate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("update_leave"))
):
    leave = db.query(EmployeeLeave).filter(EmployeeLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    # Employee can update only own pending leave
    if current_user.role not in ["admin", "hr", "manager"]:
        if leave.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="You cannot update this leave")
        if leave.status != "pending":
            raise HTTPException(status_code=400, detail="Only pending leaves can be updated")

    # Manager can update status of direct reports (approval/reject)
    if current_user.role == "manager":
        employee = db.query(Employee).filter(Employee.id == leave.employee_id).first()
        if employee.parent_id != current_user.id:
            raise HTTPException(status_code=403, detail="You cannot update this leave")

    for key, value in updated.model_dump(exclude_unset=True).items():
        setattr(leave, key, value)

    try:
        db.commit()
        db.refresh(leave)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating leave: {e}")

    return leave

# -------- DELETE LEAVE --------
@router.delete("/{leave_id}")
def delete_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("delete_leave"))
):
    leave = db.query(EmployeeLeave).filter(EmployeeLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    # Employee can delete own pending leave
    if current_user.role not in ["admin", "hr", "manager"]:
        if leave.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="You cannot delete this leave")
        if leave.status != "pending":
            raise HTTPException(status_code=400, detail="Only pending leaves can be deleted")

    # Manager can delete leave of direct reports
    if current_user.role == "manager":
        employee = db.query(Employee).filter(Employee.id == leave.employee_id).first()
        if employee.parent_id != current_user.id:
            raise HTTPException(status_code=403, detail="You cannot delete this leave")

    try:
        db.delete(leave)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting leave: {e}")

    return {"message": "Leave deleted successfully"}
