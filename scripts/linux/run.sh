#!/bin/bash

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

# Navigate to project root (assuming script is in scripts/linux)
cd "$(dirname "$0")/../.."

echo -e "${GREEN}=== Starting Portfolio Bot (Local) ===${NC}"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please run scripts/linux/setup.sh first."
    exit 1
fi

# Activate venv and run
source .venv/bin/activate
echo -e "${GREEN}Virtual environment activated.${NC}"

# Check for MongoDB (Basic check)
if ! pgrep -x "mongod" > /dev/null; then
    echo "Warning: MongoDB does not seem to be running locally. Bot might fail to connect if using localhost."
fi

echo "Starting Bot..."
python -m src.bot
