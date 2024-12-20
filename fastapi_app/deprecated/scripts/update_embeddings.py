import asyncio

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from chatlse.embeddings import compute_text_embedding
from chatlse.clients import create_embed_client
from chatlse.postgres_engine import create_postgres_engine
from fastapi_app.postgres_models import Item


async def update_embeddings():
    engine = await create_postgres_engine()
    embed_model = await create_embed_client()

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        async with session.begin():
            items = (await session.scalars(select(Item))).all()

            for item in items:
                item.embedding = await compute_text_embedding(
                    item.to_str_for_embedding(),
                    embed_model=embed_model
                )

            await session.commit()


if __name__ == "__main__":
    load_dotenv(override=True)
    asyncio.run(update_embeddings())
