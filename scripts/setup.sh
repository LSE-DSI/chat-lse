#!/bin/bash
set -e

# Install dependencies
pip install -e .

# Initialize postgres database
python fastapi_app/setup_postgres_database.py
python fastapi_app/setup_postgres_seeddata.py
