#!/bin/sh
echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations completed"