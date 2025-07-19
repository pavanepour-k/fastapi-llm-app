"""
Custom exception classes and error handlers
Reference: https://fastapi.tiangolo.com/tutorial/handling-errors/
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import logging

templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


class BaseAppException(Exception):
    """
    Base exception class for application-specific errors.
    
    Single Responsibility: Common exception interface
    """
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(BaseAppException):
    """
    Exception for authentication failures.
    
    Single Responsibility: Authentication error representation
    """
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(BaseAppException):
    """
    Exception for authorization failures.
    
    Single Responsibility: Authorization error representation
    """
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ValidationError(BaseAppException):
    """
    Exception for validation errors.
    
    Single Responsibility: Validation error representation
    """
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class NotFoundError(BaseAppException):
    """
    Exception for resource not found errors.
    
    Single Responsibility: Not found error representation
    """
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class RateLimitError(BaseAppException):
    """
    Exception for rate limiting errors.
    
    Single Responsibility: Rate limit error representation
    """
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


class LLMServiceError(BaseAppException):
    """
    Exception for LLM service errors.
    
    Single Responsibility: LLM service error representation
    """
    
    def __init__(self, message: str = "LLM service error"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


class VectorStoreError(BaseAppException):
    """
    Exception for vector store errors.
    
    Single Responsibility: Vector store error representation
    """
    
    def __init__(self, message: str = "Vector store error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


# Error handlers
async def app_exception_handler(request: Request, exc: BaseAppException):
    """
    Handler for application-specific exceptions.
    
    Single Responsibility: Application exception handling
    """
    logger.error(f"Application error: {exc.message}")
    
    # Return JSON for API requests, HTML for web requests
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "type": type(exc).__name__}
        )
    else:
        return templates.TemplateResponse(
            "errors/error.html",
            {
                "request": request,
                "status_code": exc.status_code,
                "message": exc.message
            },
            status_code=exc.status_code
        )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for HTTP exceptions.
    
    Single Responsibility: HTTP exception handling
    """
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    else:
        return templates.TemplateResponse(
            "errors/error.html",
            {
                "request": request,
                "status_code": exc.status_code,
                "message": exc.detail
            },
            status_code=exc.status_code
        )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handler for unexpected exceptions.
    
    Single Responsibility: General exception handling
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    else:
        return templates.TemplateResponse(
            "errors/error.html",
            {
                "request": request,
                "status_code": 500,
                "message": "An unexpected error occurred"
            },
            status_code=500
        )

