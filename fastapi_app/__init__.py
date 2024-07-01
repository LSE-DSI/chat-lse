import contextlib
import logging
import os

from dotenv import load_dotenv
from environs import Env
from fastapi import FastAPI

from .globals import global_storage
from .clients import create_chat_client, create_embed_client
from .postgres_engine import create_postgres_engine_from_env

logger = logging.getLogger("ragapp")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(override=True)

    engine = await create_postgres_engine_from_env()
    global_storage.engine = engine

    chat_client, chat_model = await create_chat_client()
    global_storage.chat_client = chat_client
    global_storage.chat_model = chat_model

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

    from . import api_routes  # noqa

    app.include_router(api_routes.router)

    if os.environ.get("STATIC_DIR"):
        print(os.environ.get("STATIC_DIR"))
        from . import frontend_routes  # noqa
        app.mount("/", frontend_routes.router)

    return app
