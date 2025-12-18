#!/bin/bash

echo "Waiting for database to be ready..."
sleep 10

echo "Creating shop database tables..."
python manage.py create_database

echo "Starting Owner Flask application..."
python application.py