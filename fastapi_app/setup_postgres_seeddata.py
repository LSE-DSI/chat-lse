import argparse
import asyncio
import json
import logging
import os

import sqlalchemy.exc
from dotenv import load_dotenv
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker


from fastapi_app.postgres_engine import create_postgres_engine_from_args, create_postgres_engine_from_env
from fastapi_app.postgres_models import Doc 

logger = logging.getLogger("ragapp")


async def seed_data(engine):

    # Create session for database operations
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:

        # Delete existing data in tables (assuming cascading is set up in foreign key)
        await session.execute(delete(Doc))
        await session.commit()

        # Load JSON data
        # This resolves to the path <workspace>/chat-lse/fastapi_app/setup_postgres_seeddata.py
        current_dir = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(current_dir, "..", "data", "seed_lse_data.jsonl")

        with open(filepath) as f:
            pdf_data = json.load(f)

        for pdf_entry in pdf_data:
            pdf = Doc(
                id=pdf_entry["id"],
                doc_id=pdf_entry["doc_id"],
                chunk_id=pdf_entry["chunk_id"],
                type=pdf_entry["type"],
                name=pdf_entry["name"],
                description=pdf_entry["description"],
                content=pdf_entry["content"],
                url=pdf_entry["url"], 
                embedding=pdf_entry["embedding"],
            )
            session.add(pdf)
        try:
            await session.commit()
            logger.info("Database seeded successfully.")
        except sqlalchemy.exc.IntegrityError as e:
            logger.error(f"Failed to seed database: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Populate database with seed data")
    parser.add_argument("--host", type=str, help="Postgres host")
    parser.add_argument("--username", type=str, help="Postgres username")
    parser.add_argument("--password", type=str, help="Postgres password")
    parser.add_argument("--database", type=str, help="Postgres database")
    parser.add_argument("--sslmode", type=str, help="Postgres sslmode")

    args = parser.parse_args()
    if args.host is None:
        engine = await create_postgres_engine_from_env()
    else:
        engine = await create_postgres_engine_from_args(args)

    await seed_data(engine)
    await engine.dispose()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv(override=True)
    asyncio.run(main())