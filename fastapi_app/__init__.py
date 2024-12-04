import os
import contextlib
import logging

from dotenv import load_dotenv
from environs import Env
from fastapi import FastAPI

from .globals import global_storage
from chatlse.clients import create_chat_client, create_embed_client
from chatlse.postgres_engine import create_postgres_engine_from_env

from .logger import logger 
from .middleware import LogMiddleware 

logger = logging.getLogger("ragapp")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(override=True)

    engine = await create_postgres_engine_from_env()
    global_storage.engine = engine

    chat_client, chat_model = await create_chat_client()
    global_storage.chat_client = chat_client
    global_storage.chat_model = chat_model
    global_storage.to_summarise = True
    global_storage.embedding_type = os.getenv("EMBEDDING_TYPE", "title_embeddings")
    with_user_context = os.getenv("WITH_USER_CONTEXT", False)
    global_storage.with_user_context = True if with_user_context.lower()=="true" else False 
    
    logger.info(f"Model Selected: {global_storage.chat_model}")
    logger.info(f"Embedding Type: {global_storage.embedding_type}")
    logger.info(f"With User Context: {global_storage.with_user_context}")

    embed_model = await create_embed_client()
    global_storage.embed_model = embed_model
    try:
        global_storage.context_window_override = int(os.getenv("CHAT_MODEL_CONTEXT_WINDOW_SIZE"))
    except:
        global_storage.context_window_override = None

    yield

    await engine.dispose()


def create_app():
    env = Env()

    if not os.getenv("RUNNING_IN_PRODUCTION"):
        env.read_env(".env")
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    app = FastAPI(docs_url="/docs", lifespan=lifespan)
    app.add_middleware(LogMiddleware)
    logger.info("Start API ...")

    from . import api_routes  # noqa

    app.include_router(api_routes.router)

    if os.environ.get("STATIC_DIR"):
        print(os.environ.get("STATIC_DIR"))
        from . import frontend_routes  # noqa
        app.mount("/", frontend_routes.router)

    return app