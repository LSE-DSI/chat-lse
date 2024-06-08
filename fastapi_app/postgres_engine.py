import logging
import os

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger("ragapp")


async def create_postgres_engine(*, host, username, database, password, sslmode, port=5432) -> AsyncEngine:
    
    logger.info("Authenticating to PostgreSQL using password...")

    # DATABASE_URI = f"postgresql+asyncpg://{username}:{password}@{host}/{database}"

    query = {}
    if sslmode:
        query["ssl"]=sslmode

    url_object = URL.create(
        "postgresql+asyncpg",
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        query=query
    )

    engine = create_async_engine(
        url_object,
        echo=False,
    )

    return engine


async def create_postgres_engine_from_env() -> AsyncEngine:

    engine = await create_postgres_engine(
        host=os.environ["POSTGRES_HOST"],
        username=os.environ["POSTGRES_USERNAME"],
        database=os.environ["POSTGRES_DATABASE"],
        password=os.environ["POSTGRES_PASSWORD"],
        sslmode=os.environ.get("POSTGRES_SSL"),
        port=os.getenv("POSTGRES_PORT", 5432),
    )

    return engine


async def create_postgres_engine_from_args(args) -> AsyncEngine:

    engine = await create_postgres_engine(
        host=args.host,
        username=args.username,
        database=args.database,
        password=args.password,
        sslmode=args.sslmode,
        port=args.port
    )

    return engine
