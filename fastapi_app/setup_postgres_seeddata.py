import argparse
import asyncio
import json
import logging
import os

import sqlalchemy.exc
from dotenv import load_dotenv
from sqlalchemy import select, text, delete
from sqlalchemy.ext.asyncio import async_sessionmaker

from fastapi_app.postgres_engine import create_postgres_engine_from_args, create_postgres_engine_from_env
from fastapi_app.postgres_models import Item

logger = logging.getLogger("ragapp")

async def seed_data(engine):
    async with engine.begin() as conn:
        # Check if the Item table exists
        result = await conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'items')"
            )
        )
        if not result.scalar():
            logger.error("Items table does not exist. Please run the database setup script first.")
            return

        # Delete all entries in the Item table
        await conn.execute(delete(Item))
        await conn.commit()

        # Check if the delete operation was successful
        count_result = await conn.execute(select([func.count()]).select_from(Item))
        count = count_result.scalar()
        if count == 0:
            logger.info("Successfully deleted all entries in the Items table.")
        else:
            logger.warning(f"Failed to delete all entries, {count} entries remain.")

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "seed_lse_data.json")) as f:
            catalog_items = json.load(f)
            for catalog_item in catalog_items:
                item_id = int(catalog_item["Id"])
                item = await session.execute(select(Item).filter(Item.id == item_id))
                if item.scalars().first():
                    continue
                item = Item(
                    id=item_id,
                    name=catalog_item["Name"],
                    description=catalog_item["Description"],
                    embedding=catalog_item["Embedding"],
                    link=catalog_item["Link"]
                )
                session.add(item)

            try:
                await session.commit()
            except sqlalchemy.exc.IntegrityError:
                pass

    logger.info("Items table seeded successfully.")


async def main():
    parser = argparse.ArgumentParser(description="Create database schema")
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
    logging.basicConfig(level=logging.WARNING)
    logger.setLevel(logging.INFO)
    load_dotenv(override=True)
    asyncio.run(main())
