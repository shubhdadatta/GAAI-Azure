#!/bin/bash

# Start FastAPI backend in background
python -m uvicorn main:app --host 127.0.0.1 --port 8000 &

# Start frontend server
cd static
python -m http.server 8080 --bind 0.0.0.0 &

# Wait for both processes
wait