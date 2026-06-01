#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🌈 PRISM — Pipeline for Redshift Inspection & Source Management"
echo "=============================================================="

# Check if data root is set
if [ -z "$PRISM_DATA_ROOT" ]; then
    PRISM_DATA_ROOT="${SCRIPT_DIR}/../data"
    echo "⚠  PRISM_DATA_ROOT not set, using default: ${PRISM_DATA_ROOT}"
fi

if [ ! -d "$PRISM_DATA_ROOT" ]; then
    echo "❌ Data directory not found: ${PRISM_DATA_ROOT}"
    echo "   Set PRISM_DATA_ROOT to your data directory:"
    echo "   export PRISM_DATA_ROOT=/path/to/sapphires_data"
    exit 1
fi

echo "📁 Data root: ${PRISM_DATA_ROOT}"

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install -r "${SCRIPT_DIR}/requirements.txt" -q

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd "${SCRIPT_DIR}/frontend"
npm install --silent

# Build frontend
echo "🔨 Building frontend..."
npm run build --silent

cd "${SCRIPT_DIR}"

# Start backend (which also serves frontend static files)
echo "🚀 Starting PRISM server..."
echo "   → http://localhost:8000"
uvicorn backend.main:app --host 0.0.0.0 --port 8000
