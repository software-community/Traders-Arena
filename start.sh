#!/bin/bash
# Render startup script

# Start the application with gunicorn
exec gunicorn --bind 0.0.0.0:$PORT app:app
