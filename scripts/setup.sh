#!/bin/bash
set -e

# Install dependencies
pip install -e .

# Initialize postgres database
python3 fastapi_app/setup_postgres_database.py
python3 fastapi_app/setup_postgres_seeddata.py
