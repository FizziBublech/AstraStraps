#!/bin/bash

# Start script for Reamaze API Bridge
# Usage: ./start.sh [development|production]

MODE=${1:-development}

echo "🚀 Starting Reamaze API Bridge in $MODE mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your settings:"
    echo "cp .env.example .env"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Set mode-specific environment variables
if [ "$MODE" = "production" ]; then
    export FLASK_DEBUG=False
    export LOG_LEVEL=WARNING
    echo "🏭 Starting in production mode with Gunicorn..."
    gunicorn -w 4 -b 0.0.0.0:5000 main:app
else
    export FLASK_DEBUG=True
    export LOG_LEVEL=INFO
    echo "🛠️  Starting in development mode..."
    python main.py
fi 