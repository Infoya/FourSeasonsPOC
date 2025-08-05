#!/bin/bash

echo "🚀 Starting Four Seasons Assistant Demo..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo "🔧 Starting backend server on port 8100..."
cd /Users/kameshinfoya/PycharmProjects/FourSeasonsAssistant
source .venv/bin/activate
uvicorn api:app --port 8100 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "🎨 Starting frontend server on port 3000..."
cd demo-frontend
npm start &
FRONTEND_PID=$!

echo "✅ Demo started successfully!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8100"
echo "📚 API Docs: http://localhost:8100/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait 