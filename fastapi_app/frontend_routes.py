import os
# from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount, Route, Router


static_dir = username=os.environ.get("STATIC_DIR") 


async def index(request) -> FileResponse:
    return FileResponse(os.path.join(static_dir, "index.html"))


async def favicon(request):
    return FileResponse(os.path.join(static_dir, "favicon.ico"))


router = Router(
    routes=[
        Route("/", endpoint=index),
        Route("/favicon.ico", endpoint=favicon),
        Mount("/assets", app=StaticFiles(directory=os.path.join(static_dir, "assets")), name="static_assets"),
    ]
)
