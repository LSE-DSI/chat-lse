from fastapi import Request

async def log_middleware(request: Request, call_next):
    from .logger import logger  # Import logger here to avoid circular import
    
    log_dict = {
        'url': request.url.path, 
        'method': request.method
    }
    logger.info(log_dict, extra=log_dict)

    response = await call_next(request)
    return response
