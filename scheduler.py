from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from models import Employee, Role, Shift, Schedule, Holiday, EmployeeLeave
from typing import List, Dict
import uuid

class ShiftScheduler:
    """
    Static shift scheduler that assigns shifts to employees based on:
    - Role work days and limits
    - Shift templates (day_of_week, start_time, end_time)
    - Employee availability and skills
    - Holidays and approved leaves
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_day_of_week(self, date: datetime.date) -> int:
        """Convert date to day_of_week (1=Monday, 7=Sunday)"""
        return date.isoweekday()
    
    def is_holiday(self, date: datetime.date, location: str = None) -> bool:
        """Check if date is a holiday"""
        query = self.db.query(Holiday).filter(Holiday.date == date)
        if location:
            query = query.filter((Holiday.location == location) | (Holiday.location.is_(None)))
        return query.first() is not None
    
    def has_leave(self, employee_id: uuid.UUID, date: datetime.date) -> bool:
        """Check if employee has approved leave on date"""
        leave = self.db.query(EmployeeLeave).filter(
            EmployeeLeave.employee_id == employee_id,
            EmployeeLeave.date == date,
            EmployeeLeave.approval_status == 'APPROVED'
        ).first()
        return leave is not None
    
    def is_available(self, employee: Employee, date: datetime.date, shift: Shift) -> bool:
        """Check if employee is available for the shift"""
        # Check if employee is active
        if not employee.is_active:
            return False
        
        # Check if employee has leave
        if self.has_leave(employee.id, date):
            return False
        
        # Check role work days
        day_name = date.strftime('%a')
        if employee.role.work_days and day_name not in employee.role.work_days:
            return False
        
        # Check employee availability (if specified)
        if employee.availability:
            day_key = str(self.get_day_of_week(date))
            if day_key in employee.availability:
                avail = employee.availability[day_key]
                if not avail.get('available', True):
                    return False
        
        # Check skills match (if shift requires skills)
        if shift.skills_required:
            employee_skills = employee.skills or []
            required_skills = shift.skills_required
            if not all(skill in employee_skills for skill in required_skills):
                return False
        
        return True
    
    def calculate_hours(self, start_time: time, end_time: time) -> float:
        """Calculate hours between two times"""
        start_dt = datetime.combine(datetime.today(), start_time)
        end_dt = datetime.combine(datetime.today(), end_time)
        
        # Handle overnight shifts
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        duration = end_dt - start_dt
        return duration.total_seconds() / 3600
    
    def get_weekly_scheduled_hours(self, employee_id: uuid.UUID, start_date: datetime.date) -> float:
        """Calculate total scheduled hours for the week"""
        week_start = start_date - timedelta(days=start_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        schedules = self.db.query(Schedule).filter(
            Schedule.employee_id == employee_id,
            Schedule.date >= week_start,
            Schedule.date <= week_end
        ).all()
        
        total_hours = 0
        for schedule in schedules:
            total_hours += self.calculate_hours(schedule.start_time, schedule.end_time)
        
        return total_hours
    
    def generate_schedule(
        self, 
        role_id: uuid.UUID, 
        start_date: datetime.date, 
        end_date: datetime.date,
        location: str = None
    ) -> Dict:
        """
        Generate schedules for all employees in a role for a date range
        
        Algorithm:
        1. Get all shifts for the role
        2. For each day in range:
           - Get shifts for that day_of_week
           - Skip if holiday
           - Assign shifts to available employees (priority-based)
        """
        
        # Get role and validate
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return {"error": "Role not found"}
        
        # Get all employees for this role
        employees = self.db.query(Employee).filter(
            Employee.role_id == role_id,
            Employee.is_active == True
        ).all()
        
        if not employees:
            return {"error": "No active employees found for this role"}
        
        # Get all shifts for this role
        shifts = self.db.query(Shift).filter(Shift.role_id == role_id).all()
        
        if not shifts:
            return {"error": "No shifts defined for this role"}
        
        created_schedules = []
        skipped_days = []
        
        current_date = start_date
        while current_date <= end_date:
            # Skip holidays
            if self.is_holiday(current_date, location):
                skipped_days.append({
                    "date": current_date.isoformat(),
                    "reason": "Holiday"
                })
                current_date += timedelta(days=1)
                continue
            
            # Get shifts for this day of week
            day_of_week = self.get_day_of_week(current_date)
            day_shifts = [s for s in shifts if s.day_of_week == day_of_week]
            
            # Sort shifts by priority (higher priority first)
            day_shifts.sort(key=lambda x: x.priority or 0, reverse=True)
            
            for shift in day_shifts:
                # Find available employees for this shift
                available_employees = [
                    emp for emp in employees
                    if self.is_available(emp, current_date, shift)
                ]
                
                # Check weekly hours limit
                available_employees = [
                    emp for emp in available_employees
                    if not role.weekly_hours_limit or 
                    self.get_weekly_scheduled_hours(emp.id, current_date) + 
                    self.calculate_hours(shift.start_time, shift.end_time) <= float(role.weekly_hours_limit)
                ]
                
                if not available_employees:
                    skipped_days.append({
                        "date": current_date.isoformat(),
                        "shift": shift.name,
                        "reason": "No available employees"
                    })
                    continue
                
                # Simple assignment: take first available employee
                # In production, you might want round-robin or load balancing
                selected_employee = available_employees[0]
                
                # Check if schedule already exists
                existing = self.db.query(Schedule).filter(
                    Schedule.employee_id == selected_employee.id,
                    Schedule.date == current_date
                ).first()
                
                if existing:
                    skipped_days.append({
                        "date": current_date.isoformat(),
                        "employee": selected_employee.name,
                        "reason": "Already scheduled"
                    })
                    continue
                
                # Create schedule
                schedule = Schedule(
                    id=uuid.uuid4(),
                    employee_id=selected_employee.id,
                    shift_id=shift.id,
                    date=current_date,
                    start_time=shift.start_time,
                    end_time=shift.end_time,
                    is_custom=False
                )
                
                self.db.add(schedule)
                created_schedules.append({
                    "date": current_date.isoformat(),
                    "employee": selected_employee.name,
                    "shift": shift.name,
                    "start_time": shift.start_time.isoformat(),
                    "end_time": shift.end_time.isoformat()
                })
            
            current_date += timedelta(days=1)
        
        # Commit all schedules
        self.db.commit()
        
        return {
            "created": len(created_schedules),
            "skipped": len(skipped_days),
            "schedules": created_schedules,
            "skipped_details": skipped_days
        }
