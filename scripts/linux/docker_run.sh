#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")/../.."

echo "=== Starting Portfolio Bot (Docker) ==="
docker-compose up --build -d
echo "Bot started in background. Use 'docker-compose logs -f' to see logs."
