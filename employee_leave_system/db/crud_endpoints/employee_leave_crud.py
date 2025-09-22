from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from db.models import EmployeeLeave
from db.database import get_db
from pydantic import BaseModel

# ----------------- SCHEMAS -----------------
class EmployeeLeaveBase(BaseModel):
    employee_id: int
    from_date: datetime
    to_date: datetime
    reason: str | None = None

class EmployeeLeaveCreate(EmployeeLeaveBase):
   parent_id: int 

class EmployeeLeaveRead(EmployeeLeaveBase):
    id: int
    status: str
    approved_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True 
    }

# ----------------- ROUTER -----------------
router = APIRouter()

# -------- EMPLOYEE LEAVE CRUD --------
@router.post("/leaves/", response_model=EmployeeLeaveRead)
def request_leave(leave: EmployeeLeaveCreate, db: Session = Depends(get_db)):
    db_leave = EmployeeLeave(**leave.model_dump())
    db.add(db_leave)
    try:
        db.commit()
        db.refresh(db_leave)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_leave

@router.get("/leaves/", response_model=List[EmployeeLeaveRead])
def get_leaves(db: Session = Depends(get_db)):
    return db.query(EmployeeLeave).all()

@router.get("/leaves/{leave_id}", response_model=EmployeeLeaveRead)
def get_leave(leave_id: int, db: Session = Depends(get_db)):
    leave = db.query(EmployeeLeave).filter(EmployeeLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    return leave

@router.put("/leaves/{leave_id}", response_model=EmployeeLeaveRead)
def update_leave(leave_id: int, updated: EmployeeLeaveCreate, db: Session = Depends(get_db)):
    leave = db.query(EmployeeLeave).filter(EmployeeLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    for key, value in updated.model_dump().items():
        setattr(leave, key, value)
    try:
        db.commit()
        db.refresh(leave)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return leave

@router.delete("/leaves/{leave_id}")
def delete_leave(leave_id: int, db: Session = Depends(get_db)):
    leave = db.query(EmployeeLeave).filter(EmployeeLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    try:
        db.delete(leave)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Leave deleted successfully"}
