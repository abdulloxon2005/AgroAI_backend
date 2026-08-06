from typing import Any, Callable, Dict, Union
from fastapi import Request, status
from fastapi.responses import JSONResponse

class AppException(Exception):
    """Base application exception."""
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal Server Error",
        error_code: str = "INTERNAL_ERROR"
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(self.detail)

class AuthenticationError(AppException):
    """Exception raised for authentication errors."""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )

class NotFoundError(AppException):
    """Exception raised when a resource is not found."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )

class ValidationError(AppException):
    """Exception raised for validation errors."""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )

class AIServiceError(AppException):
    """Exception raised for AI service errors."""
    def __init__(self, detail: str = "AI service error occurred"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            error_code="AI_SERVICE_ERROR"
        )

class WeatherServiceError(AppException):
    """Exception raised for weather service errors."""
    def __init__(self, detail: str = "Weather service error occurred"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            error_code="WEATHER_SERVICE_ERROR"
        )

class UnauthorizedException(AppException):
    """Exception raised for unauthorized access."""
    def __init__(self, detail: str = "Ruxsat berilmagan"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )

class NotFoundException(AppException):
    """Exception raised when a resource is not found."""
    def __init__(self, detail: str = "Topilmadi"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )

class ForbiddenException(AppException):
    """Exception raised for forbidden access."""
    def __init__(self, detail: str = "Ruxsat yo'q"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )

class BadRequestException(AppException):
    """Exception raised for bad requests."""
    def __init__(self, detail: str = "Noto'g'ri so'rov"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BAD_REQUEST"
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions with a generic 500 response."""
    import structlog
    import traceback
    traceback.print_exc()
    logger = structlog.get_logger()
    logger.exception("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Ichki server xatosi: {type(exc).__name__} - {str(exc)}", "error_code": "INTERNAL_ERROR"}
    )


exception_handlers: Dict[Union[int, type[Exception]], Callable] = {
    AppException: app_exception_handler,
    Exception: generic_exception_handler,
}
