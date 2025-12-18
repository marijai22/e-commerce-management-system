#!/bin/bash

echo "Waiting for database to be ready..."
sleep 10

echo "Starting Customer Flask application..."
python application.py