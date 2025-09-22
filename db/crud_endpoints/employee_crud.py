from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import datetime

from db.models import Employee
from db.database import get_db
from pydantic import BaseModel

# ----------------- SCHEMAS -----------------
class EmployeeBase(BaseModel):
    name: str
    email: str
    position: str | None = None
    parent_id: int | None = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeRead(EmployeeBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {
        "from_attributes": True  # Pydantic v2 replacement for orm_mode
    }

# ----------------- ROUTER -----------------
router = APIRouter()

# -------- EMPLOYEE CRUD --------
@router.post("/employees/", response_model=EmployeeRead)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    db_emp = Employee(**employee.model_dump())
    db.add(db_emp)
    try:
        db.commit()
        db.refresh(db_emp)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_emp

@router.get("/employees/", response_model=List[EmployeeRead])
def get_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()

@router.get("/employees/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@router.put("/employees/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: int, updated: EmployeeCreate, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    for key, value in updated.model_dump().items():
        setattr(emp, key, value)
    try:
        db.commit()
        db.refresh(emp)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return emp

@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    try:
        db.delete(emp)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Employee deleted successfully"}
