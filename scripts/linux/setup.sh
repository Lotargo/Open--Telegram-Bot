#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure we are in the project root
cd "$(dirname "$0")/../.." || exit

echo -e "${GREEN}=== Portfolio Bot Setup (Linux/macOS) ===${NC}"

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

# 2. Check Poetry
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry not found. Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# 3. Configure Poetry
echo -e "${GREEN}Configuring Poetry to create in-project venv...${NC}"
poetry config virtualenvs.in-project true

# 4. Install Dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
poetry install --no-root

# 5. Setup .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env file from example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}.env file created! Please edit it with your real API keys.${NC}"
    else
        echo -e "${RED}Error: .env.example not found.${NC}"
    fi
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo -e "To run the bot locally, use: ${YELLOW}./scripts/linux/run.sh${NC}"
echo -e "To run with Docker, use: ${YELLOW}./scripts/linux/docker_run.sh${NC}"
