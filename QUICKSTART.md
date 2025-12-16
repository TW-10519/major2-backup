# Quick Start Guide

## Setup (5 minutes)

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your database URL
DATABASE_URL=postgresql://user:password@localhost:5432/shift_management
SECRET_KEY=your-secret-key-change-this-in-production

# Create database
createdb shift_management

# Start server
python main.py
```

### 2. Initialize Admin

Open new terminal:
```bash
curl -X POST http://localhost:8000/api/auth/init-admin
```

### 3. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## First Login

1. Open browser: `http://localhost:5173`
2. Login with:
   - **Username:** admin
   - **Password:** admin123
   - **User Type:** Admin

## Quick Demo Setup

### As Admin:

1. **Create Department:**
   - Go to Departments tab
   - Click "Add Department"
   - Name: "Engineering"
   - Location: "HQ"

2. **Create Manager:**
   - Go to Managers tab
   - Click "Add Manager"
   - Name: "John Manager"
   - Username: "manager1"
   - Password: "password123"
   - Department: "Engineering"

3. **Logout**

### As Manager (login as manager1/password123):

1. **Create Role:**
   - Go to Roles tab
   - Click "Add Role"
   - Name: "Software Engineer"
   - Work Days: "Mon,Tue,Wed,Thu,Fri"
   - Break Minutes: 60
   - Employment Type: "Full Time"

2. **Create Shift:**
   - Go to Shifts tab
   - Click "Add Shift"
   - Name: "Morning Shift"
   - Role: "Software Engineer"
   - Day of Week: 1 (Monday)
   - Start Time: "09:00"
   - End Time: "17:00"
   - (Repeat for days 2-5 for Tue-Fri)

3. **Create Employee:**
   - Go to Employees tab
   - Click "Add Employee"
   - Name: "Alice Developer"
   - Username: "alice"
   - Password: "password123"
   - Role: "Software Engineer"

4. **Generate Schedules:**
   - Go to Schedules tab
   - Click "Generate Schedules"
   - Role: "Software Engineer"
   - Start Date: [Today]
   - End Date: [7 days from today]
   - Click Save

5. **Logout**

### As Employee (login as alice/password123):

1. **View Schedule:**
   - See your generated schedules

2. **Clock In (if today is a work day):**
   - Click "Clock In" button in Today's Schedule

3. **Clock Out (after working):**
   - Click "Clock Out" button

4. **Request Leave:**
   - Go to Leaves tab
   - Click "Request Leave"
   - Select date, type, duration
   - Submit

## API Testing

Test the API directly:

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","user_type":"admin"}'

# Get departments (replace TOKEN with the access_token from login)
curl http://localhost:8000/api/admin/departments \
  -H "Authorization: Bearer TOKEN"
```

## Common Tasks

### Reset Admin Password
```bash
# In Python shell
from database import SessionLocal
from models import Admin
from auth import get_password_hash

db = SessionLocal()
admin = db.query(Admin).filter(Admin.username == "admin").first()
admin.password_hash = get_password_hash("newpassword")
db.commit()
```

### View All Tables
```bash
# In PostgreSQL
psql shift_management
\dt
SELECT * FROM admin;
```

### Clear All Data (Development Only!)
```bash
# In PostgreSQL
psql shift_management
TRUNCATE TABLE employee_leave, overtime, attendance, schedule, 
  shift, employee, role, manager, department, holiday, admin CASCADE;
```

## Troubleshooting

**Can't create database:**
```bash
# Make sure PostgreSQL is running
sudo service postgresql start  # Linux
brew services start postgresql # Mac
```

**Port 8000 already in use:**
```bash
# Change port in main.py:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Port 5173 already in use:**
```bash
# Change port in vite.config.js:
server: { port: 3000 }
```

**CORS errors:**
- Backend and frontend must be running
- Check CORS settings in backend/main.py
- Clear browser cache

## Next Steps

- Create more departments and managers
- Set up multiple roles with different shift patterns
- Add holidays for your region
- Configure role limits and overtime rules
- Test the complete workflow from scheduling to attendance

Enjoy managing your shifts! 🚀
