#!/bin/bash

echo "🚀 Shift Management System - Setup Script"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL 12 or higher."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Setup Backend
echo "📦 Setting up Backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Create .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Please update .env file with your database credentials"
    echo "   DATABASE_URL=postgresql://user:password@localhost:5432/shift_management"
    read -p "Press enter to continue after updating .env..."
fi

cd ..

# Setup Frontend
echo ""
echo "📦 Setting up Frontend..."
cd frontend

npm install
echo "✅ Frontend dependencies installed"

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create PostgreSQL database: createdb shift_management"
echo "2. Start backend: cd backend && source venv/bin/activate && python main.py"
echo "3. Initialize admin: curl -X POST http://localhost:8000/api/auth/init-admin"
echo "4. Start frontend: cd frontend && npm run dev"
echo "5. Open browser: http://localhost:5173"
echo "6. Login with admin/admin123"
echo ""
echo "For more details, see README.md and QUICKSTART.md"
