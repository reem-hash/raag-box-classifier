#!/bin/bash

echo "🚀 Starting RAAG Box Condition Classifier..."

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable not set"
    echo "Please set it with: export OPENAI_API_KEY='sk-...'"
    exit 1
fi

echo "✅ OpenAI API key detected"

# Create necessary directories
mkdir -p images
echo "📁 Created images directory"

# Start FastAPI backend in background
echo "🔧 Starting FastAPI backend on port 7861..."
uvicorn api_enhanced:app --host 0.0.0.0 --port 7861 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:7861/ > /dev/null; then
    echo "✅ Backend running (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start Gradio UI
echo "🎨 Starting Gradio UI on port 7860..."
python gradio_app_enhanced.py

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
