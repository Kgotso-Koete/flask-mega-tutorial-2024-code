#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Cleaning up Microblog Docker environment...${NC}"

# Stop and remove Docker Compose services
echo -e "${YELLOW}Stopping Docker Compose services...${NC}"
docker-compose down

# Remove individual containers (in case they were created outside of compose)
echo -e "${YELLOW}Removing individual containers...${NC}"
docker rm -f mysql redis elasticsearch microblog rq-worker 2>/dev/null || true

# Remove Docker Compose containers specifically
echo -e "${YELLOW}Removing Docker Compose containers...${NC}"
docker-compose rm -f 2>/dev/null || true

# Optional: Remove volumes (uncomment if you want to delete all data)
echo -e "${YELLOW}Do you want to remove volumes (this will delete all database data)? [y/N]${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    docker-compose down -v
    docker volume rm microblog_mysql_data 2>/dev/null || true
    echo -e "${RED}⚠️  All data volumes removed!${NC}"
fi

# Optional: Remove images
echo -e "${YELLOW}Do you want to remove built images? [y/N]${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    docker image rm microblog_web microblog_rq-worker microblog:latest 2>/dev/null || true
    echo -e "${YELLOW}Built images removed${NC}"
fi

# Remove network
echo -e "${YELLOW}Removing networks...${NC}"
docker network rm microblog_microblog-network microblog-network 2>/dev/null || true

# Show remaining containers and networks
echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo -e "${BLUE}Remaining containers:${NC}"
docker ps -a --filter "name=microblog\|mysql\|redis\|elasticsearch" --format "table {{.Names}}\t{{.Status}}"
echo -e "${BLUE}Remaining networks:${NC}"
docker network ls --filter "name=microblog"