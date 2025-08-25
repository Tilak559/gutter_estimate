#!/bin/bash

# 🏠 Gutter Estimate Pro - Service Startup Script
# This script starts both the backend API and frontend React app

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes on a port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        print_warning "Killing existing processes on port $port"
        kill -9 $pids 2>/dev/null || true
        sleep 2
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down services..."
    
    # Kill backend
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping backend (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping frontend (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes on our ports
    kill_port 8000
    kill_port 3000
    
    print_success "All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Main startup sequence
main() {
    echo -e "${BLUE}"
    echo "🏠 Gutter Estimate Pro - Service Startup"
    echo "========================================"
    echo -e "${NC}"
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_error "Python is not installed. Please install Python 3.7+ first."
        exit 1
    fi
    
    # Check if Node.js is available
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 16+ first."
        exit 1
    fi
    
    # Check if npm is available
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    print_success "All prerequisites are met"
    
    # Check if we're in the right directory
    if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
        print_error "Please run this script from the root directory (gutter_estimate/)"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
        source venv/bin/activate
        print_status "Installing backend dependencies..."
        pip install -r backend/requirements.txt
    else
        if [ -d "venv" ]; then
            source venv/bin/activate
        else
            source .venv/bin/activate
        fi
    fi
    
    # Check if frontend dependencies are installed
    if [ ! -d "frontend/node_modules" ]; then
        print_warning "Frontend dependencies not found. Installing..."
        cd frontend
        npm install
        cd ..
    fi
    
    # Kill any existing processes on our ports
    print_status "Checking for existing processes..."
    kill_port 8000
    kill_port 3000
    
    # Start backend
    print_status "Starting backend API server..."
    cd backend
    
    # Start backend in background
    python main.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    print_success "Backend started with PID: $BACKEND_PID"
    
    # Wait for backend to be ready
    if ! wait_for_service "http://localhost:8000/docs" "Backend API"; then
        print_error "Backend failed to start. Check backend.log for details."
        exit 1
    fi
    
    # Start frontend
    print_status "Starting frontend React app..."
    cd frontend
    
    # Start frontend in background
    npm start > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    print_success "Frontend started with PID: $FRONTEND_PID"
    
    # Wait for frontend to be ready
    if ! wait_for_service "http://localhost:3000" "Frontend App"; then
        print_error "Frontend failed to start. Check frontend.log for details."
        exit 1
    fi
    
    # Final status
    echo ""
    echo -e "${GREEN}🎉 All services are running successfully!${NC}"
    echo ""
    echo -e "${BLUE}Services:${NC}"
    echo -e "  🔧 Backend API:  ${GREEN}http://localhost:8000${NC}"
    echo -e "  📚 API Docs:     ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  🎨 Frontend App: ${GREEN}http://localhost:3000${NC}"
    echo ""
    echo -e "${BLUE}Logs:${NC}"
    echo -e "  Backend:  ${YELLOW}tail -f backend.log${NC}"
    echo -e "  Frontend: ${YELLOW}tail -f frontend.log${NC}"
    echo ""
    echo -e "${BLUE}To stop all services:${NC} Press Ctrl+C"
    echo ""
    
    # Keep script running and monitor services
    while true; do
        # Check if services are still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            break
        fi
        
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            break
        fi
        
        sleep 5
    done
}

# Run main function
main "$@"
