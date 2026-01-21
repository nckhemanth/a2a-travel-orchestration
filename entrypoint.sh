#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure we're in the right directory
cd /app || exit 1

echo "Starting A2A Travel Orchestration in Docker..."

# Create uploads directory (artifacts will use /tmp which is always writable)
mkdir -p /app/uploads
chmod -R 755 /app/uploads

# Start the agent orchestrator/server manager in the background
# This script spawns the 3 fastAPI servers (Reader, Analyst, Visualizer)
python scripts/start_all_agents.py &

# Wait briefly to ensure ports binding starts
sleep 5

# Start the Streamlit App
# Hugging Face Spaces expects the app to be served on port 7860
echo "Starting Streamlit on port 7860..."
exec streamlit run src/ui/app.py --server.port 7860 --server.address 0.0.0.0
