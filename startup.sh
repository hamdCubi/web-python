#!/bin/bash

# Run Gunicorn with Uvicorn workers
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:main_app --bind 0.0.0.0:8000
