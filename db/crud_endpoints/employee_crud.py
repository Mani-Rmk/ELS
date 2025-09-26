from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
from db.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate
from db.models import Employee
from db.database import get_db
from utils.email_utils import hash_password
from dependencies import require_permission
from core import security

# ----------------- ROUTER -----------------
router = APIRouter(prefix="/employees", tags=["Employees"])

# -------- CREATE EMPLOYEE --------
@router.post("/", response_model=EmployeeRead)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("create_employee"))
):
    hashed_pwd = hash_password(employee.password)
    db_emp = Employee(
        name=employee.name,
        email=employee.email,
        password_hash=hashed_pwd,
        position=employee.position,
        parent_id=employee.parent_id,
        role=employee.role
    )
    db.add(db_emp)
    try:
        db.commit()
        db.refresh(db_emp)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_emp

# -------- BULK UPLOAD EMPLOYEES --------
@router.post("/upload", response_model=List[int], summary="Bulk upload employees via Excel")
def upload_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("upload_employees"))
):
    if not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="File must be .xls or .xlsx")
    
    try:
        df = pd.read_excel(file.file)
        required_columns = {"name", "email", "password"}
        if not required_columns.issubset(df.columns):
            raise HTTPException(
                status_code=400,
                detail=f"Excel must contain columns: {required_columns}"
            )

        db_emps = []
        existing_emails = {email for (email,) in db.query(Employee.email).all()}

        for _, row in df.iterrows():
            if row["email"] in existing_emails:
                continue

            # Non-admin cannot create HR/Admin
            role = row.get("role", "employee")
            if current_user.role != "admin" and role in ["hr", "admin"]:
                role = "employee"

            hashed_pwd = hash_password(row["password"])
            emp = Employee(
                name=row["name"],
                email=row["email"],
                password_hash=hashed_pwd,
                position=row.get("position"),
                parent_id=row.get("parent_id"),
                role=role
            )
            db.add(emp)
            db_emps.append(emp)
            existing_emails.add(row["email"])

        db.commit()
        for emp in db_emps:
            db.refresh(emp)
        return [emp.id for emp in db_emps]

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# -------- GET ALL EMPLOYEES --------
@router.get("/", response_model=List[EmployeeRead])
def get_employees(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("view_all_employee"))
):
    if current_user.role in ["hr", "admin"]:
        return db.query(Employee).all()
    elif current_user.role == "manager":
        return db.query(Employee).filter(Employee.parent_id == current_user.id).all()
    else:
        return [current_user]

# -------- GET SINGLE EMPLOYEE --------
@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("view_employee"))
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role == "manager" and emp.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot view this employee")
    return emp

# -------- UPDATE EMPLOYEE --------
@router.put("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int,
    updated: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("update_employee"))
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role == "manager" and emp.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot update this employee")

    for key, value in updated.model_dump(exclude_unset=True).items():
        if key == "password" and value:
            emp.password_hash = hash_password(value)
        else:
            setattr(emp, key, value)

    try:
        db.commit()
        db.refresh(emp)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return emp

# -------- DELETE EMPLOYEE --------
@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(security.get_current_user),
    allowed: bool = Depends(require_permission("delete_employee"))
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if emp.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")

    if current_user.role == "manager" and emp.parent_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot delete this employee")

    try:
        db.delete(emp)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Employee deleted successfully"}
