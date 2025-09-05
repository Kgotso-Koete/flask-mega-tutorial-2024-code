#!/bin/bash

# start-worker.sh - Start the RQ worker for background tasks
# Run this script in a separate terminal to handle background tasks

set -e  # Exit on any error

echo "Starting RQ Worker for background tasks..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate
echo "Virtual environment activated"

# Check if Redis is running
if ! redis-cli ping | grep -q "PONG"; then
    echo "Redis is not running. Starting Redis..."
    sudo systemctl start redis
fi

echo "Starting RQ worker..."
echo "Worker will process tasks from the 'microblog-tasks' queue"
echo "Press Ctrl+C to stop the worker"
echo ""

# Start the RQ worker
rq worker microblog-tasks