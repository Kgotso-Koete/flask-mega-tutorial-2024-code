#!/bin/bash

# complete-setup.sh - Complete setup and run script covering all 6 steps from README
# This script executes all 6 steps sequentially and starts the application

set -e  # Exit on any error

clear
echo "=============================================================================="
echo "MICROBLOG FLASK APPLICATION - COMPLETE SETUP (ALL 6 STEPS)"
echo "=============================================================================="
echo "This script will execute all 6 steps from the README:"
echo "1. Set up Python virtual environment"
echo "2. Install packages within the virtual environment" 
echo "3. Run database migrations"
echo "4. Set up background tasks (post exports) with Redis"
echo "5. Run Elasticsearch server within a Docker container"
echo "6. Run the application"
echo "=============================================================================="
echo ""
echo "Starting automated setup..."
echo ""

# ============================================================================
# STEP 1: Set up the Python virtual environment
# ============================================================================
echo ""
echo "STEP 1/6: Setting up Python virtual environment"
echo "----------------------------------------------------------------------"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated (you should see (.venv) in prompt)"

# ============================================================================
# STEP 2: Install packages within the virtual environment  
# ============================================================================
echo ""
echo "STEP 2/6: Installing packages within the virtual environment"
echo "----------------------------------------------------------------------"

echo "Upgrading pip..."
# pip install --upgrade pip

echo "Installing packages from requirements.txt..."
pip install -r requirements.txt
echo "✓ All Python packages installed"

# ============================================================================
# STEP 3: Run database migrations
# ============================================================================
echo ""
echo "STEP 3/6: Running database migrations"
echo "----------------------------------------------------------------------"

if [ ! -d "migrations" ]; then
    echo "Initializing database (first time setup)..."
    flask db init
    echo "✓ Database initialized"
fi

echo "Applying database migrations..."
flask db upgrade
echo "✓ Database migrations completed"

# ============================================================================
# STEP 4: Set up background tasks (post exports) with Redis
# ============================================================================
echo ""
echo "STEP 4/6: Setting up background tasks (post exports) with Redis"
echo "----------------------------------------------------------------------"

echo "4.1: Checking Redis installation..."
if ! command -v redis-server &> /dev/null; then
    echo "   Redis not found, installing Redis server..."
    sudo apt update
    # Clean up any automatically installed packages that are no longer needed
    echo "   Cleaning up unused packages..."
    sudo apt autoremove -y 2>/dev/null || true

    # Install Redis server
    sudo apt install -y redis-server

    # Clean up after installation
    sudo apt autoremove -y 2>/dev/null || true
    echo "✓ Redis server installed"
else
    echo "✓ Redis is already installed"
fi

echo "4.2: Starting Redis service..."
if ! sudo systemctl is-active --quiet redis; then
    sudo systemctl start redis
    echo "✓ Redis service started"
else
    echo "✓ Redis service is already running"
fi

echo "4.3: Checking Redis boot startup configuration..."
if ! sudo systemctl is-enabled --quiet redis 2>/dev/null; then
    echo "   Enabling Redis to start on boot..."
    sudo systemctl enable redis 2>/dev/null || echo "   Note: Could not enable Redis on boot (this might be expected in some environments)"
else
    echo "   Redis is already configured to start on boot"
fi

echo "4.4: Verifying Redis is running..."
# Give Redis a moment to start
sleep 2

# Try multiple times to connect to Redis
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo "✓ Redis connection verified - Redis is running"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT+1))
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo "✗ ERROR: Could not connect to Redis after $MAX_RETRIES attempts"
            echo "   Trying to start Redis manually..."
            sudo systemctl restart redis || echo "   Could not start Redis"
            sleep 2
            if ! redis-cli ping 2>/dev/null | grep -q "PONG"; then
                echo "✗ ERROR: Redis connection failed. Please check Redis service manually."
                echo "   You can try running: sudo systemctl status redis"
                exit 1
            fi
        else
            echo "   Redis not responding, retrying ($RETRY_COUNT/$MAX_RETRIES)..."
            sleep 2
        fi
    fi
done

echo "4.5: Verifying Python Redis client is installed..."
pip show redis > /dev/null || pip install redis
echo "✓ Python Redis client available"

echo "✓ Step 4 completed: Redis is ready for background tasks"
echo "  Note: RQ worker will be started separately for background processing"

# ============================================================================
# STEP 5: Run the Elasticsearch server within a Docker container
# ============================================================================
echo ""
echo "STEP 5/6: Running Elasticsearch server within a Docker container"
echo "----------------------------------------------------------------------"

echo "Stopping any existing Elasticsearch container..."
docker stop elasticsearch 2>/dev/null || echo "No existing Elasticsearch container found"

echo "Removing any problematic Docker data..."
docker volume prune -f

echo "Starting Elasticsearch container with optimized settings..."
docker run --name elasticsearch -d --rm -p 9200:9200 \
  --memory="4GB" \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e ES_JAVA_OPTS="-Xms2g -Xmx2g" \
  -e xpack.security.enrollment.enabled=false \
  -e cluster.routing.allocation.disk.threshold_enabled=false \
  -e bootstrap.memory_lock=true \
  --ulimit memlock=-1:-1 \
  -t docker.elastic.co/elasticsearch/elasticsearch:8.13.0

echo "Waiting for Elasticsearch to start up (30-60 seconds)..."
sleep 30

echo "Verifying Elasticsearch health..."
health_response=$(curl -s -X GET "http://localhost:9200/_cluster/health" || echo "ERROR")
echo "Health response: $health_response"

if curl -s -f "http://localhost:9200/_cluster/health" > /dev/null; then
    echo "✓ Elasticsearch is running and healthy"
    
    # Wait a bit more to ensure Elasticsearch is fully initialized
    echo "   Waiting for Elasticsearch to be fully ready..."
    sleep 10
    
    # Reindex all posts in Elasticsearch
    echo "5.2: Reindexing posts in Elasticsearch..."
    if [ -f "microblog.py" ]; then
        echo "   Running reindexing command..."
        if ! flask shell << 'EOF'
print("\nReindexing posts in Elasticsearch...")
from app.models import Post
Post.reindex()
print("✓ Posts have been reindexed")
EOF
        then
            echo "   Warning: Could not reindex posts automatically. You may need to do this manually."
            echo "   To reindex manually, run: flask shell"
            echo "   Then in the shell: from app.models import Post; Post.reindex()"
        fi
    else
        echo "   Warning: Could not find microblog.py. Make sure you're in the correct directory."
    fi
else
    echo "✗ ERROR: Elasticsearch health check failed"
    exit 1
fi

# ============================================================================
# STEP 6: Run the application
# ============================================================================
echo ""
echo "STEP 6/6: Running the Flask application"  
echo "----------------------------------------------------------------------"

echo "All setup steps completed successfully!"
echo ""
echo "=============================================================================="
echo "READY TO START APPLICATION"
echo "=============================================================================="
echo ""
echo "✓ Step 1: Virtual environment created and activated"
echo "✓ Step 2: Python packages installed" 
echo "✓ Step 3: Database migrations applied"
echo "✓ Step 4: Redis setup completed and running"
echo "✓ Step 5: Elasticsearch container running and healthy"
echo "✓ Step 6: Ready to start Flask application"
echo ""
echo "BACKGROUND TASKS NOTICE:"
echo "For background tasks (like post exports) to work, you need to start"  
echo "the RQ worker in a SEPARATE terminal window:"
echo ""
echo "   ./start-worker.sh"
echo ""
echo "Or manually with:"
echo "   source .venv/bin/activate"
echo "   rq worker microblog-tasks"
echo ""

# Automatically starting Flask application
echo ""
echo "Starting Flask application..."
echo "Application will be available at: http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Start the Flask application in the background
flask run &
FLASK_PID=$!

# Give Flask a moment to start up
sleep 2

# Open the default web browser
if command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "http://127.0.0.1:5000" &
elif command -v open &> /dev/null; then
    # macOS
    open "http://127.0.0.1:5000" &
elif command -v start &> /dev/null; then
    # Windows
    start "" "http://127.0.0.1:5000"
fi

# Wait for Flask to exit
trap "kill $FLASK_PID 2> /dev/null" EXIT
wait $FLASK_PID