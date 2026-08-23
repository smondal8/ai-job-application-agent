#!/usr/bin/env bash

echo "Stopping AI Job Application Agent services..."

# 1. Stop backend (uvicorn)
BACKEND_PIDS=$(pgrep -f "uvicorn app.main:app" || true)
if [ -n "$BACKEND_PIDS" ]; then
    echo "Stopping FastAPI backend (PID: $BACKEND_PIDS)..."
    kill $BACKEND_PIDS 2>/dev/null || true
    echo "Backend stopped."
else
    echo "No running FastAPI backend process found."
fi

# 2. Stop frontend (vite)
FRONTEND_PIDS=$(pgrep -f "vite" || true)
if [ -n "$FRONTEND_PIDS" ]; then
    echo "Stopping Vite frontend (PID: $FRONTEND_PIDS)..."
    kill $FRONTEND_PIDS 2>/dev/null || true
    echo "Frontend stopped."
else
    echo "No running Vite frontend process found."
fi

# Verify ports are clear
echo ""
echo "Checking port availability:"
if lsof -i :8000 > /dev/null 2>&1; then
    echo "WARNING: Port 8000 is still in use."
else
    echo "Port 8000 is free."
fi

if lsof -i :5173 > /dev/null 2>&1; then
    echo "WARNING: Port 5173 is still in use."
else
    echo "Port 5173 is free."
fi

echo "Stop completed."
