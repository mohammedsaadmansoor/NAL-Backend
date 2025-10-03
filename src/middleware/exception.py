from fastapi import Request, HTTPException
from pydantic import ValidationError, BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.settings import settings
from src.utils.logging import get_logger
from src.services.utils.exceptions import APIException

import json
# sdk = AnalyticsSDK(credentials_dict=settings.goole_firestore_service_account_dict)

logger = get_logger(__name__)

class ErrorResponseModel(BaseModel):
    """Standardized error response model."""
    success: bool = False
    exception_type: str
    message: str
    error_code: str | None = None
    stack: str | None = None

class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions with standardized responses."""
    
    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        # Read and store the request body
        body_bytes = await request.body()
        request.state.body_bytes = body_bytes 
        try:
            request.state.body_json = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except json.JSONDecodeError:
            request.state.body_json = {}

        # Extract email/email_id and store in state
        body_json = request.state.body_json
        email_value = body_json.get("email") or body_json.get("email_id") or ""
        request.state.email_value = email_value

        try:
            return await call_next(request)
        except Exception as e:
            # Initialize stack trace for dev environment
            stack_trace = None
            if settings.app.environment == "dev":
                import traceback
                stack_trace = traceback.format_exc()

            # Map exception types to status codes, log levels, messages, and error codes
            exception_map = {
                APIException: {
                    "status_code": 400,
                    "log_func": logger.warning,
                    "message": lambda exc: exc.message,
                    "error_code": "API_ERROR",
                },
                ValidationError: {
                    "status_code": 422,
                    "log_func": logger.warning,
                    "message": lambda exc: "Validation error occurred",
                    "error_code": "VALIDATION_ERROR",
                },
                HTTPException: {
                    "status_code": lambda exc: exc.status_code,
                    "log_func": logger.info,
                    "message": lambda exc: exc.detail,
                    "error_code": None,
                },
            }

            # Find matching exception type or use default
            config = exception_map.get(type(e), {
                "status_code": 500,
                "log_func": logger.error,
                "message": lambda exc: "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR",
            })

            # Log the exception
            config["log_func"](f"{e.__class__.__name__}: {config['message'](e)}", extra={
                "request_path": request.url.path,
                "request_method": request.method,
                "exception_type": e.__class__.__name__,
            })

            # Build response
            response = ErrorResponseModel(
                exception_type=e.__class__.__name__,
                message=config["message"](e),
                error_code=config["error_code"],
                stack=stack_trace,
            )

            status_code = config["status_code"](e) if callable(config["status_code"]) else config["status_code"]

            # Use cached email
            # sdk.log_error(user_id=request.state.email_value, error_details=response.dict())
            return JSONResponse(status_code=status_code, content=response.dict())

# Backward compatibility alias
ExceptionResponseModel = ErrorResponseModel