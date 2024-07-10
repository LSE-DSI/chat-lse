from fastapi import Request
import json

async def log_middleware(request: Request, call_next):
    from .logger import logger  # Import logger here to avoid circular import
    log_dict = {
        'url': request.url.path, 
        'method': request.method,
        'client': request.client.host
    }
    logger.info("Request received", extra=log_dict)

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
        try:
            response_body = [section async for section in response.__dict__['body_iterator']]
            response.__setattr__('body_iterator', iter(response_body))
            logger.info(f"Response body: {response_body[0].decode()}", extra=log_dict)
        except Exception as e:
            logger.error(f"Error logging response body: {e}", extra=log_dict)

    return response
