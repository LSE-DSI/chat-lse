import argparse
import asyncio
import json
import logging
import os

import sqlalchemy.exc
from dotenv import load_dotenv
from sqlalchemy import select, text, delete
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.dialects.postgresql import JSONB


from fastapi_app.postgres_engine import create_postgres_engine_from_args, create_postgres_engine_from_env
from fastapi_app.postgres_models import PDF, Item

logger = logging.getLogger("ragapp")


async def seed_data(engine):

    # Create session for database operations
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:

        # Delete existing data in tables (assuming cascading is set up in foreign key)
        await session.execute(delete(Item))
        await session.execute(delete(PDF))
        await session.commit()

        # Load JSON data
        current_dir = os.path.dirname(os.path.realpath(__file__))

        with open(os.path.join(current_dir, "seed_lse_data_0.json")) as f:
            pdf_data = json.load(f)

        for pdf_entry in pdf_data:
            pdf = PDF(
                id=pdf_entry["Id"],
                name=pdf_entry["Name"],
                description=pdf_entry["Description"],
                link=pdf_entry["Link"]
            )
            session.add(pdf)

            # Each chunk in the PDF becomes an item in the Items table
            for chunk in pdf_entry["Chunks"]:
                item = Item(
                    type=chunk["Type"],
                    name=chunk["Name"],
                    description=chunk["Description"],
                    embedding=chunk["Embedding"],
                    pdf_id=pdf_entry["Id"]  # Link item back to the PDF
                )
                session.add(item)

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