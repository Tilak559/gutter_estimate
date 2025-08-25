#!/bin/bash

# 🏠 Gutter Estimate Pro - Service Status Checker

echo "🏠 Gutter Estimate Pro - Service Status"
echo "======================================="
echo

# Check Backend
echo "🔧 Backend API (Port 8000):"
if curl -s http://localhost:8000/docs >/dev/null 2>&1; then
    echo "   ✅ Running - http://localhost:8000"
    echo "   📚 Docs: http://localhost:8000/docs"
else
    echo "   ❌ Not running"
fi
echo

# Check Frontend
echo "🎨 Frontend App (Port 3000):"
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "   ✅ Running - http://localhost:3000"
else
    echo "   ❌ Not running"
fi
echo

# Check Processes
echo "📊 Process Status:"
BACKEND_PID=$(lsof -ti:8000 2>/dev/null)
FRONTEND_PID=$(lsof -ti:3000 2>/dev/null)

if [ ! -z "$BACKEND_PID" ]; then
    echo "   🔧 Backend PID: $BACKEND_PID"
else
    echo "   🔧 Backend: No process found"
fi

if [ ! -z "$FRONTEND_PID" ]; then
    echo "   🎨 Frontend PID: $FRONTEND_PID"
else
    echo "   🎨 Frontend: No process found"
fi
echo

# Summary
if [ ! -z "$BACKEND_PID" ] && [ ! -z "$FRONTEND_PID" ]; then
    echo "🎉 All services are running!"
    echo
    echo "🌐 Access your application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
else
    echo "⚠️  Some services are not running."
    echo "   Run './start_services.sh' to start all services."
fi
