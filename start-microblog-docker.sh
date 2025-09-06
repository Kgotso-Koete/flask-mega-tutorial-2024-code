#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Microblog application...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}⚠️  .env file not found. Please create it with your configuration.${NC}"
    echo -e "${BLUE}ℹ️  You can copy the template: cp .env.example .env${NC}"
    exit 1
fi

# Stop and remove existing containers
echo -e "${BLUE}🧹 Cleaning up existing containers...${NC}"
docker-compose down
# Also remove any standalone containers that might conflict
docker rm -f mysql redis elasticsearch microblog rq-worker 2>/dev/null || true

# Check for port conflicts and warn user
echo -e "${BLUE}🔍 Checking for port conflicts...${NC}"
if lsof -i:6379 >/dev/null 2>&1; then
    echo -e "${RED}⚠️  Port 6379 is in use (likely Redis). Stopping host Redis service...${NC}"
    sudo systemctl stop redis-server 2>/dev/null || sudo service redis-server stop 2>/dev/null || true
fi

# Build and start all services
echo -e "${BLUE}🔨 Building and starting services...${NC}"
docker-compose up --build -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 15

# Check individual service status
echo -e "${BLUE}🔍 Checking service status...${NC}"
docker-compose ps

# Check if the web service is running
if docker-compose ps web | grep -q "Up"; then
    echo -e "${GREEN}✅ Microblog is running!${NC}"
    echo -e "${GREEN}🌐 Opening browser to http://localhost:8000${NC}"
    
    # Open browser based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open http://localhost:8000
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:8000
        elif command -v gnome-open > /dev/null; then
            gnome-open http://localhost:8000
        else
            echo -e "${BLUE}Please open http://localhost:8000 in your browser${NC}"
        fi
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        start http://localhost:8000
    else
        echo -e "${BLUE}Please open http://localhost:8000 in your browser${NC}"
    fi
    
    echo -e "${GREEN}📋 Useful commands:${NC}"
    echo -e "  ${BLUE}View logs:${NC} docker-compose logs -f"
    echo -e "  ${BLUE}Stop services:${NC} docker-compose down"
    echo -e "  ${BLUE}Restart services:${NC} docker-compose restart"
    echo -e "  ${BLUE}View running containers:${NC} docker-compose ps"
else
    echo -e "${RED}❌ Failed to start Microblog. Check logs with: docker-compose logs${NC}"
    exit 1
fi