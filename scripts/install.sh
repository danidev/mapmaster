#!/bin/bash

echo "Setting up MapMaster environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p assets/maps
mkdir -p assets/tokens
mkdir -p annotations

echo "MapMaster setup complete!"
echo "Use 'scripts/run.sh' to start the application"