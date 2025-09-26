from sqlalchemy import Column, Integer, String, Text, Date,Boolean, Enum, ForeignKey, TIMESTAMP,UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base

class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("employee", "manager", "hr", "admin"), default="employee")
    position = Column(String(100))
    parent_id = Column(Integer, ForeignKey("employee.id")) 

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
    leave_type = Column(Enum("sick", "casual", "earned", "unpaid"), default="casual")
    status = Column(Enum("pending", "approved", "rejected","cancelled"), default="pending")
    approved_by = Column(Integer, ForeignKey("employee.id"))
    comments = Column(Text) 

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="Present")  # Present, Absent, Leave, WFH, Holiday

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Ensure only one record per employee per day
        UniqueConstraint('employee_id', 'date', name='unique_employee_date'),
    )

class CompanyCalendar(Base):
    __tablename__ = "company_calendar"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True)
    is_holiday = Column(Boolean, nullable=False, default=False)
    holiday_name = Column(String(100))  # Optional, e.g., "Independence Day", "Weekend"

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
