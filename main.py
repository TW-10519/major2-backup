from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date, time
from typing import List, Optional
from pydantic import BaseModel
import uuid

from database import get_db, init_db
from models import (
    Admin, Manager, Department, Role, Shift, Employee, 
    Schedule, Attendance, Overtime, EmployeeLeave, Holiday
)
from auth import (
    verify_password, get_password_hash, create_access_token, 
    decode_token, Token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from scheduler import ShiftScheduler

app = FastAPI(title="Shift Management System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Initialize database on startup
@app.on_event("startup")
def startup():
    init_db()

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str
    user_type: str  # 'admin', 'manager', 'employee'

class DepartmentCreate(BaseModel):
    name: str
    location: Optional[str] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None

class ManagerCreate(BaseModel):
    name: str
    username: str
    password: str
    department_id: uuid.UUID

class ManagerUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    department_id: Optional[uuid.UUID] = None

class RoleCreate(BaseModel):
    department_id: uuid.UUID
    name: str
    work_days: List[str]
    break_minutes: int
    daily_work_hours: Optional[float] = None
    weekly_hours_limit: Optional[float] = None
    daily_max_hours: Optional[float] = None
    monthly_overtime_limit: Optional[float] = None
    employment_type: Optional[str] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    work_days: Optional[List[str]] = None
    break_minutes: Optional[int] = None
    daily_work_hours: Optional[float] = None
    weekly_hours_limit: Optional[float] = None
    daily_max_hours: Optional[float] = None
    monthly_overtime_limit: Optional[float] = None
    employment_type: Optional[str] = None

class ShiftCreate(BaseModel):
    role_id: uuid.UUID
    name: str
    day_of_week: int
    start_time: str
    end_time: str
    priority: Optional[int] = 0
    skills_required: Optional[List[str]] = None

class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    priority: Optional[int] = None
    skills_required: Optional[List[str]] = None

class EmployeeCreate(BaseModel):
    role_id: uuid.UUID
    name: str
    username: str
    password: str
    yearly_paid_leave_allowance: Optional[int] = None
    availability: Optional[dict] = None
    skills: Optional[List[str]] = None

class EmployeeUpdate(BaseModel):
    role_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    yearly_paid_leave_allowance: Optional[int] = None
    availability: Optional[dict] = None
    skills: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ScheduleCreate(BaseModel):
    employee_id: uuid.UUID
    shift_id: Optional[uuid.UUID] = None
    date: date
    start_time: str
    end_time: str
    overtime_hours: Optional[float] = 0
    is_custom: Optional[bool] = False

class ScheduleUpdate(BaseModel):
    shift_id: Optional[uuid.UUID] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    overtime_hours: Optional[float] = None

class ClockInRequest(BaseModel):
    employee_id: uuid.UUID
    date: date

class ClockOutRequest(BaseModel):
    employee_id: uuid.UUID
    date: date

class OvertimeCreate(BaseModel):
    employee_id: uuid.UUID
    date: date
    actual_hours: float
    overtime_type: str
    compensation_mode: str

class OvertimeApproval(BaseModel):
    approved_hours: Optional[float] = None
    approval_status: str

class LeaveRequest(BaseModel):
    employee_id: uuid.UUID
    leave_type: str
    date: date
    duration: str
    reason: Optional[str] = None

class LeaveApproval(BaseModel):
    approval_status: str

class HolidayCreate(BaseModel):
    name: str
    date: date
    holiday_type: str
    location: Optional[str] = None
    is_paid: Optional[bool] = True

class ScheduleGenerateRequest(BaseModel):
    role_id: uuid.UUID
    start_date: date
    end_date: date
    location: Optional[str] = None

# ============================================================================
# AUTHENTICATION DEPENDENCY
# ============================================================================

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return payload

# ============================================================================
# AUTH ROUTES
# ============================================================================

@app.post("/api/auth/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = None
    user_type = request.user_type.lower()
    
    if user_type == "admin":
        user = db.query(Admin).filter(Admin.username == request.username).first()
    elif user_type == "manager":
        user = db.query(Manager).filter(Manager.username == request.username).first()
    elif user_type == "employee":
        user = db.query(Employee).filter(Employee.username == request.username).first()
    else:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_type": user_type,
            "user_id": str(user.id)
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_type=user_type,
        user_id=str(user.id),
        name=user.name
    )

@app.post("/api/auth/init-admin")
def init_admin(db: Session = Depends(get_db)):
    """Initialize default admin user"""
    existing = db.query(Admin).filter(Admin.username == "admin").first()
    if existing:
        return {"message": "Admin already exists"}
    
    admin = Admin(
        id=uuid.uuid4(),
        name="System Admin",
        username="admin",
        password_hash=get_password_hash("admin123")
    )
    db.add(admin)
    db.commit()
    return {"message": "Admin created", "username": "admin", "password": "admin123"}

# ============================================================================
# ADMIN ROUTES - Departments
# ============================================================================

@app.get("/api/admin/departments")
def get_departments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    departments = db.query(Department).all()
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "location": d.location,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in departments
    ]

@app.post("/api/admin/departments")
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    department = Department(
        id=uuid.uuid4(),
        name=data.name,
        location=data.location
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    
    return {
        "id": str(department.id),
        "name": department.name,
        "location": department.location
    }

@app.put("/api/admin/departments/{department_id}")
def update_department(
    department_id: uuid.UUID,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    if data.name:
        department.name = data.name
    if data.location:
        department.location = data.location
    
    db.commit()
    db.refresh(department)
    
    return {
        "id": str(department.id),
        "name": department.name,
        "location": department.location
    }

@app.delete("/api/admin/departments/{department_id}")
def delete_department(
    department_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    db.delete(department)
    db.commit()
    
    return {"message": "Department deleted"}

# ============================================================================
# ADMIN ROUTES - Managers
# ============================================================================

@app.get("/api/admin/managers")
def get_managers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    managers = db.query(Manager).all()
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "username": m.username,
            "department_id": str(m.department_id),
            "department_name": m.department.name if m.department else None,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in managers
    ]

@app.post("/api/admin/managers")
def create_manager(
    data: ManagerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if username exists
    existing = db.query(Manager).filter(Manager.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    manager = Manager(
        id=uuid.uuid4(),
        name=data.name,
        username=data.username,
        password_hash=get_password_hash(data.password),
        department_id=data.department_id
    )
    db.add(manager)
    db.commit()
    db.refresh(manager)
    
    return {
        "id": str(manager.id),
        "name": manager.name,
        "username": manager.username,
        "department_id": str(manager.department_id)
    }

@app.put("/api/admin/managers/{manager_id}")
def update_manager(
    manager_id: uuid.UUID,
    data: ManagerUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    if data.name:
        manager.name = data.name
    if data.username:
        manager.username = data.username
    if data.password:
        manager.password_hash = get_password_hash(data.password)
    if data.department_id:
        manager.department_id = data.department_id
    
    db.commit()
    db.refresh(manager)
    
    return {
        "id": str(manager.id),
        "name": manager.name,
        "username": manager.username,
        "department_id": str(manager.department_id)
    }

@app.delete("/api/admin/managers/{manager_id}")
def delete_manager(
    manager_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    db.delete(manager)
    db.commit()
    
    return {"message": "Manager deleted"}

# ============================================================================
# MANAGER ROUTES - Roles
# ============================================================================

@app.get("/api/manager/roles")
def get_roles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    roles = db.query(Role).filter(Role.department_id == manager.department_id).all()
    
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "work_days": r.work_days,
            "break_minutes": r.break_minutes,
            "daily_work_hours": float(r.daily_work_hours) if r.daily_work_hours else None,
            "weekly_hours_limit": float(r.weekly_hours_limit) if r.weekly_hours_limit else None,
            "daily_max_hours": float(r.daily_max_hours) if r.daily_max_hours else None,
            "monthly_overtime_limit": float(r.monthly_overtime_limit) if r.monthly_overtime_limit else None,
            "employment_type": r.employment_type,
            "department_id": str(r.department_id)
        }
        for r in roles
    ]

@app.post("/api/manager/roles")
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    if str(data.department_id) != str(manager.department_id):
        raise HTTPException(status_code=403, detail="Can only create roles in your department")
    
    role = Role(
        id=uuid.uuid4(),
        department_id=data.department_id,
        name=data.name,
        work_days=data.work_days,
        break_minutes=data.break_minutes,
        daily_work_hours=data.daily_work_hours,
        weekly_hours_limit=data.weekly_hours_limit,
        daily_max_hours=data.daily_max_hours,
        monthly_overtime_limit=data.monthly_overtime_limit,
        employment_type=data.employment_type
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return {"id": str(role.id), "name": role.name}

@app.put("/api/manager/roles/{role_id}")
def update_role(
    role_id: uuid.UUID,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role or str(role.department_id) != str(manager.department_id):
        raise HTTPException(status_code=404, detail="Role not found in your department")
    
    if data.name:
        role.name = data.name
    if data.work_days:
        role.work_days = data.work_days
    if data.break_minutes is not None:
        role.break_minutes = data.break_minutes
    if data.daily_work_hours is not None:
        role.daily_work_hours = data.daily_work_hours
    if data.weekly_hours_limit is not None:
        role.weekly_hours_limit = data.weekly_hours_limit
    if data.daily_max_hours is not None:
        role.daily_max_hours = data.daily_max_hours
    if data.monthly_overtime_limit is not None:
        role.monthly_overtime_limit = data.monthly_overtime_limit
    if data.employment_type:
        role.employment_type = data.employment_type
    
    db.commit()
    db.refresh(role)
    
    return {"id": str(role.id), "name": role.name}

@app.delete("/api/manager/roles/{role_id}")
def delete_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    
    if not role or str(role.department_id) != str(manager.department_id):
        raise HTTPException(status_code=404, detail="Role not found")
    
    db.delete(role)
    db.commit()
    
    return {"message": "Role deleted"}

# ============================================================================
# MANAGER ROUTES - Shifts
# ============================================================================

@app.get("/api/manager/shifts")
def get_shifts(
    role_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    
    query = db.query(Shift).join(Role).filter(Role.department_id == manager.department_id)
    if role_id:
        query = query.filter(Shift.role_id == role_id)
    
    shifts = query.all()
    
    return [
        {
            "id": str(s.id),
            "role_id": str(s.role_id),
            "role_name": s.role.name if s.role else None,
            "name": s.name,
            "day_of_week": s.day_of_week,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "priority": s.priority,
            "skills_required": s.skills_required
        }
        for s in shifts
    ]

@app.post("/api/manager/shifts")
def create_shift(
    data: ShiftCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    role = db.query(Role).filter(Role.id == data.role_id).first()
    
    if not role or str(role.department_id) != str(manager.department_id):
        raise HTTPException(status_code=403, detail="Role not in your department")
    
    shift = Shift(
        id=uuid.uuid4(),
        role_id=data.role_id,
        name=data.name,
        day_of_week=data.day_of_week,
        start_time=datetime.strptime(data.start_time, "%H:%M").time(),
        end_time=datetime.strptime(data.end_time, "%H:%M").time(),
        priority=data.priority,
        skills_required=data.skills_required
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    
    return {"id": str(shift.id), "name": shift.name}

@app.put("/api/manager/shifts/{shift_id}")
def update_shift(
    shift_id: uuid.UUID,
    data: ShiftUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    shift = db.query(Shift).join(Role).filter(
        Shift.id == shift_id,
        Role.department_id == manager.department_id
    ).first()
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    if data.name:
        shift.name = data.name
    if data.day_of_week is not None:
        shift.day_of_week = data.day_of_week
    if data.start_time:
        shift.start_time = datetime.strptime(data.start_time, "%H:%M").time()
    if data.end_time:
        shift.end_time = datetime.strptime(data.end_time, "%H:%M").time()
    if data.priority is not None:
        shift.priority = data.priority
    if data.skills_required is not None:
        shift.skills_required = data.skills_required
    
    db.commit()
    db.refresh(shift)
    
    return {"id": str(shift.id), "name": shift.name}

@app.delete("/api/manager/shifts/{shift_id}")
def delete_shift(
    shift_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    shift = db.query(Shift).join(Role).filter(
        Shift.id == shift_id,
        Role.department_id == manager.department_id
    ).first()
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    db.delete(shift)
    db.commit()
    
    return {"message": "Shift deleted"}

# ============================================================================
# MANAGER ROUTES - Employees
# ============================================================================

@app.get("/api/manager/employees")
def get_employees(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    employees = db.query(Employee).join(Role).filter(
        Role.department_id == manager.department_id
    ).all()
    
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "username": e.username,
            "role_id": str(e.role_id),
            "role_name": e.role.name if e.role else None,
            "is_active": e.is_active,
            "monthly_overtime_used": float(e.monthly_overtime_used) if e.monthly_overtime_used else 0,
            "yearly_paid_leave_allowance": e.yearly_paid_leave_allowance,
            "yearly_paid_leave_used": e.yearly_paid_leave_used,
            "skills": e.skills,
            "availability": e.availability
        }
        for e in employees
    ]

@app.post("/api/manager/employees")
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    role = db.query(Role).filter(Role.id == data.role_id).first()
    
    if not role or str(role.department_id) != str(manager.department_id):
        raise HTTPException(status_code=403, detail="Role not in your department")
    
    # Check if username exists
    existing = db.query(Employee).filter(Employee.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    employee = Employee(
        id=uuid.uuid4(),
        role_id=data.role_id,
        name=data.name,
        username=data.username,
        password_hash=get_password_hash(data.password),
        yearly_paid_leave_allowance=data.yearly_paid_leave_allowance,
        availability=data.availability,
        skills=data.skills
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return {"id": str(employee.id), "name": employee.name}

@app.put("/api/manager/employees/{employee_id}")
def update_employee(
    employee_id: uuid.UUID,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    employee = db.query(Employee).join(Role).filter(
        Employee.id == employee_id,
        Role.department_id == manager.department_id
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if data.role_id:
        role = db.query(Role).filter(Role.id == data.role_id).first()
        if not role or str(role.department_id) != str(manager.department_id):
            raise HTTPException(status_code=403, detail="Role not in your department")
        employee.role_id = data.role_id
    
    if data.name:
        employee.name = data.name
    if data.username:
        employee.username = data.username
    if data.password:
        employee.password_hash = get_password_hash(data.password)
    if data.yearly_paid_leave_allowance is not None:
        employee.yearly_paid_leave_allowance = data.yearly_paid_leave_allowance
    if data.availability is not None:
        employee.availability = data.availability
    if data.skills is not None:
        employee.skills = data.skills
    if data.is_active is not None:
        employee.is_active = data.is_active
    
    db.commit()
    db.refresh(employee)
    
    return {"id": str(employee.id), "name": employee.name}

@app.delete("/api/manager/employees/{employee_id}")
def delete_employee(
    employee_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    employee = db.query(Employee).join(Role).filter(
        Employee.id == employee_id,
        Role.department_id == manager.department_id
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Soft delete
    employee.is_active = False
    db.commit()
    
    return {"message": "Employee deactivated"}

# ============================================================================
# MANAGER ROUTES - Schedules
# ============================================================================

@app.get("/api/manager/schedules")
def get_schedules(
    employee_id: Optional[uuid.UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    
    query = db.query(Schedule).join(Employee).join(Role).filter(
        Role.department_id == manager.department_id
    )
    
    if employee_id:
        query = query.filter(Schedule.employee_id == employee_id)
    if start_date:
        query = query.filter(Schedule.date >= start_date)
    if end_date:
        query = query.filter(Schedule.date <= end_date)
    
    schedules = query.all()
    
    return [
        {
            "id": str(s.id),
            "employee_id": str(s.employee_id),
            "employee_name": s.employee.name if s.employee else None,
            "shift_id": str(s.shift_id) if s.shift_id else None,
            "shift_name": s.shift.name if s.shift else None,
            "date": s.date.isoformat(),
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "overtime_hours": float(s.overtime_hours) if s.overtime_hours else 0,
            "is_custom": s.is_custom
        }
        for s in schedules
    ]

@app.post("/api/manager/schedules")
def create_schedule(
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    employee = db.query(Employee).join(Role).filter(
        Employee.id == data.employee_id,
        Role.department_id == manager.department_id
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if schedule already exists
    existing = db.query(Schedule).filter(
        Schedule.employee_id == data.employee_id,
        Schedule.date == data.date
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Schedule already exists for this date")
    
    schedule = Schedule(
        id=uuid.uuid4(),
        employee_id=data.employee_id,
        shift_id=data.shift_id,
        date=data.date,
        start_time=datetime.strptime(data.start_time, "%H:%M").time(),
        end_time=datetime.strptime(data.end_time, "%H:%M").time(),
        overtime_hours=data.overtime_hours,
        is_custom=data.is_custom
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    return {"id": str(schedule.id), "date": schedule.date.isoformat()}

@app.post("/api/manager/schedules/generate")
def generate_schedules(
    data: ScheduleGenerateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    role = db.query(Role).filter(Role.id == data.role_id).first()
    
    if not role or str(role.department_id) != str(manager.department_id):
        raise HTTPException(status_code=403, detail="Role not in your department")
    
    scheduler = ShiftScheduler(db)
    result = scheduler.generate_schedule(
        data.role_id,
        data.start_date,
        data.end_date,
        data.location
    )
    
    return result

@app.delete("/api/manager/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    schedule = db.query(Schedule).join(Employee).join(Role).filter(
        Schedule.id == schedule_id,
        Role.department_id == manager.department_id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db.delete(schedule)
    db.commit()
    
    return {"message": "Schedule deleted"}

# ============================================================================
# MANAGER ROUTES - Attendance
# ============================================================================

@app.get("/api/manager/attendance")
def get_attendance(
    employee_id: Optional[uuid.UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    
    query = db.query(Attendance).join(Employee).join(Role).filter(
        Role.department_id == manager.department_id
    )
    
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    
    attendances = query.all()
    
    return [
        {
            "id": str(a.id),
            "employee_id": str(a.employee_id),
            "employee_name": a.employee.name if a.employee else None,
            "date": a.date.isoformat(),
            "scheduled_start": a.scheduled_start.isoformat() if a.scheduled_start else None,
            "scheduled_end": a.scheduled_end.isoformat() if a.scheduled_end else None,
            "clock_in": a.clock_in.isoformat() if a.clock_in else None,
            "clock_out": a.clock_out.isoformat() if a.clock_out else None,
            "worked_hours": float(a.worked_hours) if a.worked_hours else 0,
            "overtime_hours": float(a.overtime_hours) if a.overtime_hours else 0,
            "status": a.status
        }
        for a in attendances
    ]

# ============================================================================
# MANAGER ROUTES - Overtime Approval
# ============================================================================

@app.get("/api/manager/overtime")
def get_overtime_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    
    overtimes = db.query(Overtime).join(Employee).join(Role).filter(
        Role.department_id == manager.department_id
    ).all()
    
    return [
        {
            "id": str(o.id),
            "employee_id": str(o.employee_id),
            "employee_name": o.employee.name if o.employee else None,
            "date": o.date.isoformat(),
            "actual_hours": float(o.actual_hours),
            "approved_hours": float(o.approved_hours) if o.approved_hours else None,
            "overtime_type": o.overtime_type,
            "compensation_mode": o.compensation_mode,
            "approval_status": o.approval_status,
            "created_at": o.created_at.isoformat() if o.created_at else None
        }
        for o in overtimes
    ]

@app.put("/api/manager/overtime/{overtime_id}/approve")
def approve_overtime(
    overtime_id: uuid.UUID,
    data: OvertimeApproval,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    overtime = db.query(Overtime).join(Employee).join(Role).filter(
        Overtime.id == overtime_id,
        Role.department_id == manager.department_id
    ).first()
    
    if not overtime:
        raise HTTPException(status_code=404, detail="Overtime request not found")
    
    overtime.approval_status = data.approval_status
    if data.approved_hours is not None:
        overtime.approved_hours = data.approved_hours
    else:
        overtime.approved_hours = overtime.actual_hours
    
    # If approved with COMP_OFF, create compensatory leave
    if data.approval_status == "APPROVED" and overtime.compensation_mode == "COMP_OFF":
        # Create comp-off leave (auto-approved)
        comp_off = EmployeeLeave(
            id=uuid.uuid4(),
            employee_id=overtime.employee_id,
            leave_type="COMP_OFF",
            date=overtime.date + timedelta(days=7),  # Default 7 days later
            duration="FULL_DAY",
            approval_status="APPROVED",
            source_overtime_id=overtime.id,
            reason=f"Compensatory leave for overtime on {overtime.date}"
        )
        db.add(comp_off)
    
    # Update employee overtime usage if EXTRA_PAY
    if data.approval_status == "APPROVED" and overtime.compensation_mode == "EXTRA_PAY":
        employee = overtime.employee
        employee.monthly_overtime_used = (employee.monthly_overtime_used or 0) + overtime.approved_hours
    
    db.commit()
    
    return {"message": "Overtime request processed"}

# ============================================================================
# MANAGER ROUTES - Leave Approval
# ============================================================================

@app.get("/api/manager/leaves")
def get_leave_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    
    leaves = db.query(EmployeeLeave).join(Employee).join(Role).filter(
        Role.department_id == manager.department_id
    ).all()
    
    return [
        {
            "id": str(l.id),
            "employee_id": str(l.employee_id),
            "employee_name": l.employee.name if l.employee else None,
            "leave_type": l.leave_type,
            "date": l.date.isoformat(),
            "duration": l.duration,
            "reason": l.reason,
            "approval_status": l.approval_status,
            "created_at": l.created_at.isoformat() if l.created_at else None
        }
        for l in leaves
    ]

@app.put("/api/manager/leaves/{leave_id}/approve")
def approve_leave(
    leave_id: uuid.UUID,
    data: LeaveApproval,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    manager = db.query(Manager).filter(Manager.id == uuid.UUID(current_user["user_id"])).first()
    leave = db.query(EmployeeLeave).join(Employee).join(Role).filter(
        EmployeeLeave.id == leave_id,
        Role.department_id == manager.department_id
    ).first()
    
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    leave.approval_status = data.approval_status
    
    # Update employee leave usage if approved
    if data.approval_status == "APPROVED" and leave.leave_type == "PAID":
        employee = leave.employee
        increment = 1 if leave.duration == "FULL_DAY" else 0.5
        employee.yearly_paid_leave_used = (employee.yearly_paid_leave_used or 0) + increment
    
    db.commit()
    
    return {"message": "Leave request processed"}

# ============================================================================
# MANAGER ROUTES - Holidays
# ============================================================================

@app.get("/api/manager/holidays")
def get_holidays(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    holidays = db.query(Holiday).all()
    return [
        {
            "id": str(h.id),
            "name": h.name,
            "date": h.date.isoformat(),
            "holiday_type": h.holiday_type,
            "location": h.location,
            "is_paid": h.is_paid
        }
        for h in holidays
    ]

@app.post("/api/manager/holidays")
def create_holiday(
    data: HolidayCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    holiday = Holiday(
        id=uuid.uuid4(),
        name=data.name,
        date=data.date,
        holiday_type=data.holiday_type,
        location=data.location,
        is_paid=data.is_paid
    )
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    
    return {"id": str(holiday.id), "name": holiday.name}

# ============================================================================
# EMPLOYEE ROUTES - Schedules
# ============================================================================

@app.get("/api/employee/schedules")
def get_employee_schedules(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    
    employee_id = uuid.UUID(current_user["user_id"])
    
    query = db.query(Schedule).filter(Schedule.employee_id == employee_id)
    
    if start_date:
        query = query.filter(Schedule.date >= start_date)
    if end_date:
        query = query.filter(Schedule.date <= end_date)
    
    schedules = query.all()
    
    return [
        {
            "id": str(s.id),
            "shift_name": s.shift.name if s.shift else "Custom",
            "date": s.date.isoformat(),
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "overtime_hours": float(s.overtime_hours) if s.overtime_hours else 0,
            "is_custom": s.is_custom
        }
        for s in schedules
    ]

# ============================================================================
# EMPLOYEE ROUTES - Attendance (Clock In/Out)
# ============================================================================

@app.post("/api/employee/clock-in")
def clock_in(
    data: ClockInRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    
    if str(data.employee_id) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only clock in for yourself")
    
    # Check if schedule exists
    schedule = db.query(Schedule).filter(
        Schedule.employee_id == data.employee_id,
        Schedule.date == data.date
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found for this date")
    
    # Check if already clocked in
    existing = db.query(Attendance).filter(
        Attendance.employee_id == data.employee_id,
        Attendance.date == data.date
    ).first()
    
    if existing and existing.clock_in:
        raise HTTPException(status_code=400, detail="Already clocked in")
    
    now = datetime.now().time()
    
    if existing:
        existing.clock_in = now
    else:
        attendance = Attendance(
            id=uuid.uuid4(),
            employee_id=data.employee_id,
            date=data.date,
            scheduled_start=schedule.start_time,
            scheduled_end=schedule.end_time,
            clock_in=now,
            status="PRESENT"
        )
        db.add(attendance)
    
    db.commit()
    
    return {"message": "Clocked in successfully", "time": now.isoformat()}

@app.post("/api/employee/clock-out")
def clock_out(
    data: ClockOutRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    
    if str(data.employee_id) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only clock out for yourself")
    
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == data.employee_id,
        Attendance.date == data.date
    ).first()
    
    if not attendance or not attendance.clock_in:
        raise HTTPException(status_code=400, detail="Must clock in first")
    
    if attendance.clock_out:
        raise HTTPException(status_code=400, detail="Already clocked out")
    
    now = datetime.now().time()
    attendance.clock_out = now
    
    # Calculate worked hours
    clock_in_dt = datetime.combine(data.date, attendance.clock_in)
    clock_out_dt = datetime.combine(data.date, now)
    
    if clock_out_dt < clock_in_dt:
        clock_out_dt += timedelta(days=1)
    
    duration = clock_out_dt - clock_in_dt
    worked_hours = duration.total_seconds() / 3600
    
    attendance.worked_hours = worked_hours
    
    # Calculate overtime if worked more than scheduled
    if attendance.scheduled_start and attendance.scheduled_end:
        scheduled_start_dt = datetime.combine(data.date, attendance.scheduled_start)
        scheduled_end_dt = datetime.combine(data.date, attendance.scheduled_end)
        
        if scheduled_end_dt < scheduled_start_dt:
            scheduled_end_dt += timedelta(days=1)
        
        scheduled_duration = scheduled_end_dt - scheduled_start_dt
        scheduled_hours = scheduled_duration.total_seconds() / 3600
        
        if worked_hours > scheduled_hours:
            attendance.overtime_hours = worked_hours - scheduled_hours
    
    db.commit()
    
    return {
        "message": "Clocked out successfully",
        "time": now.isoformat(),
        "worked_hours": float(worked_hours),
        "overtime_hours": float(attendance.overtime_hours) if attendance.overtime_hours else 0
    }

# ============================================================================
# EMPLOYEE ROUTES - Attendance History
# ============================================================================

@app.get("/api/employee/attendance")
def get_employee_attendance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    
    employee_id = uuid.UUID(current_user["user_id"])
    
    query = db.query(Attendance).filter(Attendance.employee_id == employee_id)
    
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    
    attendances = query.all()
    
    return [
        {
            "date": a.date.isoformat(),
            "scheduled_start": a.scheduled_start.isoformat() if a.scheduled_start else None,
            "scheduled_end": a.scheduled_end.isoformat() if a.scheduled_end else None,
            "clock_in": a.clock_in.isoformat() if a.clock_in else None,
            "clock_out": a.clock_out.isoformat() if a.clock_out else None,
            "worked_hours": float(a.worked_hours) if a.worked_hours else 0,
            "overtime_hours": float(a.overtime_hours) if a.overtime_hours else 0,
            "status": a.status
        }
        for a in attendances
    ]

# ============================================================================
# EMPLOYEE ROUTES - Overtime
# ============================================================================

@app.get("/api/employee/overtime")
def get_employee_overtime(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    
    employee_id = uuid.UUID(current_user["user_id"])
    overtimes = db.query(Overtime).filter(Overtime.employee_id == employee_id).all()
    
    return [
        {
            "id": str(o.id),
            "date": o.date.isoformat(),
            "actual_hours": float(o.actual_hours),
            "approved_hours": float(o.approved_hours) if o.approved_hours else None,
            "overtime_type": o.overtime_type,
            "compensation_mode": o.compensation_mode,
            "approval_status": o.approval_status
        }
        for o in overtimes
    ]

@app.post("/api/employee/overtime")
def request_overtime(
    data: OvertimeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    
    if str(data.employee_id) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only request overtime for yourself")
    
    overtime = Overtime(
        id=uuid.uuid4(),
        employee_id=data.employee_id,
        date=data.date,
        actual_hours=data.actual_hours,
        overtime_type=data.overtime_type,
        compensation_mode=data.compensation_mode,
        approval_status="PENDING"
    )
    db.add(overtime)
    db.commit()
    db.refresh(overtime)
    
    return {"id": str(overtime.id), "message": "Overtime request submitted"}

# ============================================================================
# EMPLOYEE ROUTES - Leave
# ============================================================================

@app.get("/api/employee/leaves")
def get_employee_leaves(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    
    employee_id = uuid.UUID(current_user["user_id"])
    leaves = db.query(EmployeeLeave).filter(EmployeeLeave.employee_id == employee_id).all()
    
    return [
        {
            "id": str(l.id),
            "leave_type": l.leave_type,
            "date": l.date.isoformat(),
            "duration": l.duration,
            "reason": l.reason,
            "approval_status": l.approval_status
        }
        for l in leaves
    ]

@app.post("/api/employee/leaves")
def request_leave(
    data: LeaveRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    
    if str(data.employee_id) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only request leave for yourself")
    
    # Check if leave already exists
    existing = db.query(EmployeeLeave).filter(
        EmployeeLeave.employee_id == data.employee_id,
        EmployeeLeave.date == data.date
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Leave already requested for this date")
    
    leave = EmployeeLeave(
        id=uuid.uuid4(),
        employee_id=data.employee_id,
        leave_type=data.leave_type,
        date=data.date,
        duration=data.duration,
        reason=data.reason,
        approval_status="PENDING"
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    
    return {"id": str(leave.id), "message": "Leave request submitted"}

@app.get("/api/employee/profile")
def get_employee_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")
    
    employee = db.query(Employee).filter(Employee.id == uuid.UUID(current_user["user_id"])).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "id": str(employee.id),
        "name": employee.name,
        "username": employee.username,
        "role_name": employee.role.name if employee.role else None,
        "department_name": employee.role.department.name if employee.role and employee.role.department else None,
        "monthly_overtime_used": float(employee.monthly_overtime_used) if employee.monthly_overtime_used else 0,
        "yearly_paid_leave_allowance": employee.yearly_paid_leave_allowance,
        "yearly_paid_leave_used": employee.yearly_paid_leave_used,
        "skills": employee.skills,
        "availability": employee.availability
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Shift Management System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
