from sqlalchemy import Boolean, Column, String, Integer, Date, Time, DateTime, Numeric, ForeignKey, CheckConstraint, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Department(Base):
    __tablename__ = "department"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    location = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    managers = relationship("Manager", back_populates="department")
    roles = relationship("Role", back_populates="department")


class Manager(Base):
    __tablename__ = "manager"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    username = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("department.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    department = relationship("Department", back_populates="managers")


class Role(Base):
    __tablename__ = "role"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("department.id"), nullable=False)
    name = Column(Text, nullable=False)
    work_days = Column(JSONB, nullable=False)
    break_minutes = Column(Integer, nullable=False)
    daily_work_hours = Column(Numeric(4, 2))
    weekly_hours_limit = Column(Numeric(4, 2))
    daily_max_hours = Column(Numeric(4, 2))
    monthly_overtime_limit = Column(Numeric(4, 2))
    employment_type = Column(Text, CheckConstraint("employment_type IN ('FULL_TIME', 'PART_TIME')"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    department = relationship("Department", back_populates="roles")
    shifts = relationship("Shift", back_populates="role")
    employees = relationship("Employee", back_populates="role")


class Shift(Base):
    __tablename__ = "shift"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("role.id"), nullable=False)
    name = Column(Text, nullable=False)
    day_of_week = Column(Integer, CheckConstraint("day_of_week BETWEEN 1 AND 7"))
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    priority = Column(Integer, default=0)
    skills_required = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    role = relationship("Role", back_populates="shifts")
    schedules = relationship("Schedule", back_populates="shift")


class Employee(Base):
    __tablename__ = "employee"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("role.id"), nullable=False)
    name = Column(Text, nullable=False)
    username = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    monthly_overtime_used = Column(Numeric(4, 2), default=0)
    yearly_paid_leave_allowance = Column(Integer)
    yearly_paid_leave_used = Column(Integer, default=0)
    availability = Column(JSONB)
    skills = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    role = relationship("Role", back_populates="employees")
    schedules = relationship("Schedule", back_populates="employee")
    attendances = relationship("Attendance", back_populates="employee")
    overtimes = relationship("Overtime", back_populates="employee")
    leaves = relationship("EmployeeLeave", back_populates="employee")


class Holiday(Base):
    __tablename__ = "holiday"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    holiday_type = Column(Text, CheckConstraint("holiday_type IN ('NATIONAL', 'REGIONAL', 'COMPANY')"))
    location = Column(Text)
    is_paid = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('date', 'location', name='uq_holiday_date_location'),)


class Schedule(Base):
    __tablename__ = "schedule"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.id"), nullable=False)
    shift_id = Column(UUID(as_uuid=True), ForeignKey("shift.id"))
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    overtime_hours = Column(Numeric(4, 2), default=0)
    is_custom = Column(Boolean, default=False)
    
    __table_args__ = (UniqueConstraint('employee_id', 'date', name='uq_schedule_employee_date'),)
    
    employee = relationship("Employee", back_populates="schedules")
    shift = relationship("Shift", back_populates="schedules")


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.id"), nullable=False)
    date = Column(Date, nullable=False)
    scheduled_start = Column(Time)
    scheduled_end = Column(Time)
    clock_in = Column(Time)
    clock_out = Column(Time)
    worked_hours = Column(Numeric(4, 2))
    overtime_hours = Column(Numeric(4, 2), default=0)
    status = Column(Text, CheckConstraint("status IN ('PRESENT', 'ABSENT')"))
    
    __table_args__ = (UniqueConstraint('employee_id', 'date', name='uq_attendance_employee_date'),)
    
    employee = relationship("Employee", back_populates="attendances")


class Overtime(Base):
    __tablename__ = "overtime"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.id"), nullable=False)
    date = Column(Date, nullable=False)
    actual_hours = Column(Numeric(4, 2), nullable=False)
    approved_hours = Column(Numeric(4, 2))
    overtime_type = Column(Text, CheckConstraint("overtime_type IN ('NORMAL', 'NIGHT', 'HOLIDAY')"))
    compensation_mode = Column(Text, CheckConstraint("compensation_mode IN ('EXTRA_PAY', 'COMP_OFF')"))
    approval_status = Column(Text, CheckConstraint("approval_status IN ('PENDING', 'APPROVED', 'REJECTED')"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('employee_id', 'date', 'overtime_type', name='uq_overtime_employee_date_type'),)
    
    employee = relationship("Employee", back_populates="overtimes")
    comp_off_leaves = relationship("EmployeeLeave", back_populates="source_overtime")


class EmployeeLeave(Base):
    __tablename__ = "employee_leave"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.id"), nullable=False)
    leave_type = Column(Text, CheckConstraint("leave_type IN ('PAID', 'UNPAID', 'COMP_OFF')"))
    date = Column(Date, nullable=False)
    duration = Column(Text, CheckConstraint("duration IN ('FULL_DAY', 'HALF_DAY')"))
    reason = Column(Text)
    approval_status = Column(Text, CheckConstraint("approval_status IN ('PENDING', 'APPROVED', 'REJECTED')"))
    source_overtime_id = Column(UUID(as_uuid=True), ForeignKey("overtime.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('employee_id', 'date', name='uq_leave_employee_date'),)
    
    employee = relationship("Employee", back_populates="leaves")
    source_overtime = relationship("Overtime", back_populates="comp_off_leaves")


# Admin user (simple table for system admin)
class Admin(Base):
    __tablename__ = "admin"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    username = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
