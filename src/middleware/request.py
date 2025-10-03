from fastapi import Request
from contextvars import ContextVar
from src.utils.logging import REQUEST_CONTEXT

# Middleware function to set REQUEST_CONTEXT
async def set_request_context(request: Request, call_next):
    """Middleware to set request context for logging."""
    token = REQUEST_CONTEXT.set(request)
    try:
        response = await call_next(request)
        return response
    finally:
        REQUEST_CONTEXT.reset(token)
