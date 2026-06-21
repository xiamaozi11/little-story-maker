#!/bin/bash
# Run script for StoryCraft

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root directory
cd "$PROJECT_DIR"

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PYTHONPATH}:${PROJECT_DIR}/src"

# Run Streamlit
streamlit run src/app.py "$@"
