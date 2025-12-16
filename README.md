# Shift Management System

A comprehensive attendance and shift management system for organizations with departments and shift-based employees.

## Features

### Admin Portal
- Create and manage departments
- Create and manage managers
- Assign managers to departments

### Manager Portal
- Create and manage roles within their department
- Define role rules (work days, limits, employment type)
- Create and manage shift templates
- Create, edit, and deactivate employees
- Assign schedules (shifts) to employees
- Auto-generate schedules using the scheduler
- View employee attendance and overtime
- Approve or reject overtime requests
- Approve or reject leave requests (paid, unpaid, comp-off)
- Manage holidays

### Employee Portal
- View assigned schedules
- Clock in and clock out for scheduled work
- View attendance history
- View overtime records
- Request overtime
- Request leave (paid, unpaid, comp-off)
- View holiday and comp-off entitlements

## Tech Stack

### Backend
- **Python 3.9+**
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary database
- **Pydantic** - Data validation
- **JWT** - Authentication

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **React Router** - Routing
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

## Project Structure

```
shift-management-system/
├── backend/
│   ├── main.py              # FastAPI application with all routes
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Database connection
│   ├── auth.py              # Authentication utilities
│   ├── scheduler.py         # Auto shift scheduling logic
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variables template
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── LoginPage.jsx
    │   │   ├── AdminPage.jsx
    │   │   ├── ManagerPage.jsx
    │   │   └── EmployeePage.jsx
    │   ├── App.jsx
    │   ├── main.jsx
    │   ├── api.js           # API client
    │   └── index.css        # Tailwind styles
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

## Installation

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Update `.env` with your database credentials:
```
DATABASE_URL=postgresql://user:password@localhost:5432/shift_management
SECRET_KEY=your-secret-key-here
```

6. Create database:
```bash
createdb shift_management
```

7. Initialize admin user:
```bash
python -c "import requests; requests.post('http://localhost:8000/api/auth/init-admin')"
```

8. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Default Credentials

After initializing the admin user:
- **Username:** admin
- **Password:** admin123
- **User Type:** Admin

## API Documentation

Once the backend is running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Usage Guide

### Admin Workflow

1. **Login** as admin
2. **Create departments** (e.g., Sales, Engineering)
3. **Create managers** and assign them to departments
4. Managers can now login and manage their departments

### Manager Workflow

1. **Login** as manager
2. **Create roles** (e.g., Sales Rep, Senior Engineer)
   - Define work days (Mon, Tue, Wed, etc.)
   - Set work hour limits
   - Set employment type
3. **Create shift templates** for each role
   - Define day of week (1=Monday, 7=Sunday)
   - Set start and end times
   - Set priority for scheduling
4. **Create employees** and assign them to roles
5. **Generate schedules** automatically or create manually
6. **Monitor attendance** and approve overtime/leave requests

### Employee Workflow

1. **Login** as employee
2. **View schedule** for upcoming shifts
3. **Clock in/out** on scheduled days
4. **Request overtime** if working extra hours
5. **Request leave** for time off
6. View attendance history and leave balance

## Scheduler Logic

The automatic scheduler (`scheduler.py`) works as follows:

1. Takes a role, start date, and end date
2. For each day in the range:
   - Skips holidays
   - Gets shifts for that day of the week
   - Finds available employees based on:
     - Active status
     - No approved leave
     - Role work days match
     - Skills match (if required)
     - Weekly hours limit not exceeded
   - Assigns shift to first available employee
3. Returns summary of created schedules and skipped days

## Database Schema

The system uses 11 main tables:
- **admin** - System administrators
- **department** - Organizational departments
- **manager** - Department managers
- **role** - Job roles with work rules
- **shift** - Shift templates
- **employee** - Workers
- **schedule** - Planned work
- **attendance** - Actual work records
- **overtime** - Overtime requests and approvals
- **employee_leave** - Leave requests and approvals
- **holiday** - Company/national holidays

## Key Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (Admin, Manager, Employee)
- Department-level isolation for managers

### Attendance Tracking
- Clock in/out functionality
- Automatic overtime calculation
- Immutable attendance records

### Leave Management
- Multiple leave types (Paid, Unpaid, Comp-off)
- Approval workflow
- Leave balance tracking
- Compensatory leave auto-generation from approved overtime

### Schedule Generation
- Automatic shift assignment
- Respects role constraints
- Considers employee availability and skills
- Holiday handling

## Development

### Adding New Features

**Backend:**
1. Add route in `main.py`
2. Update models in `models.py` if needed
3. Add validation schemas using Pydantic

**Frontend:**
1. Create components in respective page files
2. Add API calls using the `api.js` client
3. Update state management as needed

### Database Migrations

For schema changes:
1. Update `models.py`
2. Drop and recreate tables (development only):
```python
from database import engine, Base
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
```

For production, use Alembic for migrations.

## Deployment

### Backend Deployment
1. Set production environment variables
2. Use a production WSGI server (Gunicorn + Uvicorn)
3. Set up PostgreSQL database
4. Enable HTTPS

### Frontend Deployment
1. Build production bundle:
```bash
npm run build
```
2. Serve `dist` folder using Nginx or CDN
3. Update API base URL for production

## Troubleshooting

**Backend won't start:**
- Check PostgreSQL is running
- Verify database credentials in `.env`
- Ensure all dependencies are installed

**Frontend can't connect to backend:**
- Check backend is running on port 8000
- Verify CORS settings in `main.py`
- Check proxy settings in `vite.config.js`

**Authentication errors:**
- Clear localStorage and login again
- Check token expiration settings
- Verify SECRET_KEY matches between sessions

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please create an issue on the repository.
