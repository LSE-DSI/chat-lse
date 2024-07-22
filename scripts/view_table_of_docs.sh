#!/bin/bash
set -e
python -m uvicorn table:app --reload --port 8001