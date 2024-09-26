from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp 
from .logger import logger  # Import logger here to avoid circular import
import json
from starlette.responses import StreamingResponse
from typing import Callable

class LogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        log_dict = {
            'url': request.url.path, 
            'method': request.method,
            'client': request.client.host
        }
        #logger.info("Request received", extra=log_dict)

        # Exclude static files from logging.
        if request.url.path.startswith("/favicon") or request.url.path.startswith("/assets"):
            response = await call_next(request)
            return response

        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.json()
                logger.info(f"Request body: {json.dumps(body)}", extra=log_dict)
            except Exception as e:
                logger.error(f"Error logging request body: {e}", extra=log_dict)

        response = await call_next(request)

        log_dict['status_code'] = response.status_code
        logger.info("Response sent", extra=log_dict)

        if response.status_code == 200:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            #logger.info(f"Response body: {response_body.decode()}", extra=log_dict)
            response = StreamingResponse(iter([response_body]), status_code=response.status_code)
            for header, value in response.headers.items():
                response.headers[header] = value

        return response
