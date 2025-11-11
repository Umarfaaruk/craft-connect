#!/bin/bash
# Start script for Craft Connect Backend
# This script sets the correct Uvicorn configuration for large file uploads

echo "Starting Craft Connect Backend..."
echo "Max upload size: 1GB"
echo "Server will run on http://0.0.0.0:8000"

# Start uvicorn with increased limits for large file uploads
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --limit-concurrency 100 --limit-max-requests 1000 --timeout-keep-alive 300
