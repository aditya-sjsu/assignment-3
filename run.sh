#!/bin/bash

# Start the Flask backend server in the background
python app.py &

# Wait a moment for the Flask server to start
sleep 2

# Start the frontend server
python -m http.server 8000 --directory static 