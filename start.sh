#!/bin/sh

# Get the port from the environment variable
PORT=${PORT:-8000}  # Default to 8000 if PORT is not set

# Start Uvicorn with the dynamically set port
/app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT
