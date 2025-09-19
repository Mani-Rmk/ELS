from sqlalchemy import Column, Integer, String, Text, Date, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base

class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    position = Column(String(100))
    parent_id = Column(Integer, ForeignKey("employee.id"))
    
    # Auto timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    manager = relationship("Employee", remote_side=[id])


class EmployeeLeave(Base):
    __tablename__ = "employee_leave"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(Enum("pending", "approved", "rejected"), default="pending")
    approved_by = Column(Integer, ForeignKey("employee.id"))

    # Auto timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

