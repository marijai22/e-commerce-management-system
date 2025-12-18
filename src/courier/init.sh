#!/bin/bash

echo "Waiting for database to be ready..."
sleep 10

echo "Starting Courier Flask application..."
python application.py