#!/bin/bash

# GPT Researcher Startup Script
# This script starts both the backend server and the Next.js frontend

# Set the base directory to the script's location
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BASE_DIR"

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check if a process is running on a specific port
is_port_in_use() {
  if command_exists lsof; then
    lsof -i:"$1" >/dev/null 2>&1
    return $?
  elif command_exists netstat; then
    netstat -tuln | grep ":$1 " >/dev/null 2>&1
    return $?
  else
    echo "Warning: Cannot check if port $1 is in use (lsof or netstat not found)"
    return 1
  fi
}

# Function to start the backend server
start_backend() {
  echo "Starting GPT Researcher backend server..."
  
  # Check if conda environment is specified and exists
  if [ -n "$CONDA_ENV" ] && command_exists conda; then
    # Activate conda environment and start the server
    echo "Activating conda environment: $CONDA_ENV"
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV"
    
    if [ $? -ne 0 ]; then
      echo "Error: Failed to activate conda environment '$CONDA_ENV'"
      return 1
    fi
  fi
  
  # Check if port 8000 is already in use
  if is_port_in_use 8000; then
    echo "Error: Port 8000 is already in use. Backend server may already be running."
    return 1
  fi
  
  # Start the backend server
  python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
  BACKEND_PID=$!
  echo "Backend server started with PID: $BACKEND_PID"
  echo $BACKEND_PID > "$BASE_DIR/.backend.pid"
  
  # Wait a moment to ensure the server starts
  sleep 3
  
  # Check if the server is running
  if ! ps -p $BACKEND_PID > /dev/null; then
    echo "Error: Backend server failed to start"
    return 1
  fi
  
  echo "Backend server is running on http://localhost:8000"
  return 0
}

# Function to start the Next.js frontend
start_frontend() {
  echo "Starting GPT Researcher Next.js frontend..."
  
  # Check if port 3000 is already in use
  if is_port_in_use 3000; then
    echo "Error: Port 3000 is already in use. Frontend may already be running."
    return 1
  fi
  
  # Navigate to the Next.js directory
  cd "$BASE_DIR/frontend/nextjs"
  
  # Check if npm is installed
  if ! command_exists npm; then
    echo "Error: npm is not installed. Cannot start the frontend."
    return 1
  fi
  
  # Start the Next.js frontend
  npm run start &
  FRONTEND_PID=$!
  echo "Frontend started with PID: $FRONTEND_PID"
  echo $FRONTEND_PID > "$BASE_DIR/.frontend.pid"
  
  # Navigate back to the base directory
  cd "$BASE_DIR"
  
  # Wait a moment to ensure the frontend starts
  sleep 5
  
  # Check if the frontend is running
  if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "Error: Frontend failed to start"
    return 1
  fi
  
  echo "Frontend is running on http://localhost:3000"
  return 0
}

# Function to stop the services
stop_services() {
  echo "Stopping GPT Researcher services..."
  
  # Stop backend
  if [ -f "$BASE_DIR/.backend.pid" ]; then
    BACKEND_PID=$(cat "$BASE_DIR/.backend.pid")
    if ps -p $BACKEND_PID > /dev/null; then
      echo "Stopping backend server (PID: $BACKEND_PID)..."
      kill $BACKEND_PID
      rm "$BASE_DIR/.backend.pid"
    else
      echo "Backend server is not running"
      rm "$BASE_DIR/.backend.pid"
    fi
  else
    echo "No backend PID file found"
  fi
  
  # Stop frontend
  if [ -f "$BASE_DIR/.frontend.pid" ]; then
    FRONTEND_PID=$(cat "$BASE_DIR/.frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null; then
      echo "Stopping frontend (PID: $FRONTEND_PID)..."
      kill $FRONTEND_PID
      rm "$BASE_DIR/.frontend.pid"
    else
      echo "Frontend is not running"
      rm "$BASE_DIR/.frontend.pid"
    fi
  else
    echo "No frontend PID file found"
  fi
  
  echo "All services stopped"
}

# Function to check the status of the services
check_status() {
  echo "Checking GPT Researcher services status..."
  
  # Check backend
  if [ -f "$BASE_DIR/.backend.pid" ]; then
    BACKEND_PID=$(cat "$BASE_DIR/.backend.pid")
    if ps -p $BACKEND_PID > /dev/null; then
      echo "Backend server is running (PID: $BACKEND_PID)"
    else
      echo "Backend server is not running (stale PID file)"
    fi
  else
    echo "Backend server is not running (no PID file)"
  fi
  
  # Check frontend
  if [ -f "$BASE_DIR/.frontend.pid" ]; then
    FRONTEND_PID=$(cat "$BASE_DIR/.frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null; then
      echo "Frontend is running (PID: $FRONTEND_PID)"
    else
      echo "Frontend is not running (stale PID file)"
    fi
  else
    echo "Frontend is not running (no PID file)"
  fi
}

# Set the conda environment name (change this if needed)
CONDA_ENV="gpt-researcher"

# Process command line arguments
case "$1" in
  start)
    start_backend && start_frontend
    ;;
  stop)
    stop_services
    ;;
  restart)
    stop_services
    sleep 2
    start_backend && start_frontend
    ;;
  status)
    check_status
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    echo "  start   - Start both backend and frontend"
    echo "  stop    - Stop both backend and frontend"
    echo "  restart - Restart both backend and frontend"
    echo "  status  - Check the status of the services"
    exit 1
    ;;
esac

exit 0
