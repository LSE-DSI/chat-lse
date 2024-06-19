pip install -e .

docker run -itd --name chatlse-postgres -p 5432:5432 -e POSTGRES_PASSWORD=chatlse -e POSTGRES_USER=chatlse -e POSTGRES_DB=chatlse -d pgvector/pgvector:0.7.1-pg16
python fastapi_app/setup_postgres_database.py
python fastapi_app/setup_postgres_seeddata.py

Pushd frontend
npm install
