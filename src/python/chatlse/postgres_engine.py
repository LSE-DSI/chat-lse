import logging
import os

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import Engine, create_engine

logger = logging.getLogger("ragapp")


async def create_postgres_engine(*, host, port, username, database, password, sslmode) -> AsyncEngine:
    
    logger.info("Authenticating to PostgreSQL using password...")

    DATABASE_URI = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    # Specify SSL mode if needed
    if sslmode:
        DATABASE_URI += f"?ssl={sslmode}"

    engine = create_async_engine(
        DATABASE_URI,
        echo=False,
    )

    return engine


async def create_postgres_engine_from_env() -> AsyncEngine:

    engine = await create_postgres_engine(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ.get("POSTGRES_PORT", 5432),
        username=os.environ["POSTGRES_USERNAME"],
        database=os.environ["POSTGRES_DATABASE"],
        password=os.environ["POSTGRES_PASSWORD"],
        sslmode=os.environ.get("POSTGRES_SSL")
    )

    return engine


def create_postgres_engine_sync(*, host, port, username, database, password, sslmode) -> Engine:
    
    logger.info("Authenticating to PostgreSQL using password...")

    DATABASE_URI = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    # Specify SSL mode if needed
    # if sslmode:
    #     DATABASE_URI += f"?ssl={sslmode}"

    engine = create_engine(
        DATABASE_URI,
        echo=True,
    )

    return engine


def create_postgres_engine_from_env_sync() -> Engine:

    engine = create_postgres_engine_sync(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ.get("POSTGRES_PORT", 5432),
        username=os.environ["POSTGRES_USERNAME"],
        database=os.environ["POSTGRES_DATABASE"],
        password=os.environ["POSTGRES_PASSWORD"],
        sslmode=os.environ.get("POSTGRES_SSL")
    )

    return engine


async def create_postgres_engine_from_args(args) -> AsyncEngine:

    engine = await create_postgres_engine(
        host=args.host,
        username=args.username,
        database=args.database,
        password=args.password,
        sslmode=args.sslmode,
    )

    return engine
