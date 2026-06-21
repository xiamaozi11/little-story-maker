#!/bin/bash
# Quick setup script for StoryCraft

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root directory
cd "$PROJECT_DIR"

echo "📚 Setting up StoryCraft..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Setup environment file
if [ ! -f .env ]; then
    echo "🔧 Setting up .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys"
fi

echo "✅ Setup complete!"
echo "🚀 Run 'streamlit run src/app.py' to start the application"
echo "   Or use: ./scripts/run.sh"
