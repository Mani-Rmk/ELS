from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import models, database
from db.schemas import LoginRequest, TokenResponse
from core.security import verify_password, create_access_token

router = APIRouter(tags=["Login"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.Employee).filter(models.Employee.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}
