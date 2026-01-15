#!/bin/bash

# A2A Travel Orchestration - Setup & Run Script

echo "Setting up A2A Travel Orchestration..."

# Cleanup Logic: Kill old agents on ports 8001, 8002, 8003
echo "Cleaning up old processes..."
lsof -ti:8001,8002,8003 | xargs kill -9 2>/dev/null || true
rm -rf src/agents/__pycache__ src/__pycache__

# Check if uv is installed
if command -v uv &> /dev/null; then
    echo "uv detected! Using uv for blazing fast installation..."
    uv venv .venv || true
    source .venv/bin/activate
    uv pip install -r requirements.txt
else
    echo "📦 Using standard pip..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

echo "Dependencies installed!"

# Check/Create .env file
if [ ! -f .env ]; then
    echo ".env file not found!"
    echo "You can use either an OpenAI API Key OR a Euri Key."
    read -p "Enter your API Key (sk-... or euri-...): " INPUT_KEY

    if [[ "$INPUT_KEY" == sk-* ]]; then
        echo "OPENAI_API_KEY=$INPUT_KEY" > .env
        echo "Configured with OpenAI Key."
    elif [[ "$INPUT_KEY" != "" ]]; then
        echo "EUR_API_KEY=$INPUT_KEY" > .env
        echo "Configured with Euri Key."
    else
        echo "No key entered. Project may fail unless keys are in system env."
    fi
fi

# Run the project
echo "---------------------------------------------------"
echo "Starting A2A Agents (Travel Concierge, Committee, Artist)..."
echo "Starting Streamlit UI..."
echo "---------------------------------------------------"

# Start agents in background
python scripts/start_all_agents.py &
AGENTS_PID=$!

# Wait for agents to spin up
sleep 5

# Start Streamlit
streamlit run src/ui/app.py

# Cleanup on exit
kill $AGENTS_PID
