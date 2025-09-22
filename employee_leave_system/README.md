# employee_leave_system

# Employee Leave Management System

A **FastAPI-based system** to manage employee leave requests with email notifications. Employees submit leave requests, and managers can approve or reject them. All actions are stored in a MySQL database.  

---

## Features

- Submit leave requests
- Manager approval/rejection
- Email notifications with **Leave ID** and details
- MySQL database storage with SQLAlchemy

---

## Tech Stack

- **Backend:** FastAPI  
- **Database:** MySQL / MariaDB  
- **ORM:** SQLAlchemy  
- **Email:** SMTP (Gmail recommended)  
- **Python Packages:** `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pymysql`, `python-dotenv`

---

## Installation & Run

```bash
git clone https://github.com/Mani-Rmk/employee_leave_system.git
cd employee-leave-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

## API Endpoints

### Submit Leave
POST /leave/request
Request body: 
{
  "employee_id": 2,
  "from_date": "2025-09-21",
  "to_date": "2025-09-25",
  "reason": "Family vacation"
}
- Sends email to manager with Leave ID

### Approve/Reject Leave
POST /leave/approval
Request body: 
{
  "leave_id": 1,
  "approved_by": 1,
  "status": "approved"
}
- Sends email to employee about approval/rejection

