source .venv/bin/activate#!/bin/bash
set -e

# Install dependencies
pip install -e .

# For dev only
docker run -itd --name chatlse-postgres -p 5432:5432 -e POSTGRES_PASSWORD=chatlse -e POSTGRES_USER=chatlse -e POSTGRES_DB=chatlse -d pgvector/pgvector:0.7.1-pg16

# Initialize postgres database
python fastapi_app/setup_postgres_database.py
python fastapi_app/setup_postgres_seeddata.py

# Install npm dependencies for frontend
cd frontend
npm install
