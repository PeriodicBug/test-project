
```python
from typing import Any, Dict, Optional
from fastapi import HTTPException as FastAPIHTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class HTTPException(FastAPIHTTPException):
    """Base HTTP exception with additional context"""
    
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class NotFoundException(HTTPException):
    """Exception raised when a resource is not found"""
    
    def __init__(
        self,
        detail: str = "Resource not found",
        headers: Optional[Dict[str, Any]] = None,
        error_code: str = "NOT_FOUND",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class ValidationException(HTTPException):
    """Exception raised when validation fails"""
    
    def __init__(
        self,
        detail: Any = "Validation error",
        headers: Optional[Dict[str, Any]] = None,
        error_code: str = "VALIDATION_ERROR",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class UnauthorizedException(HTTPException):
    """Exception raised when authentication fails"""
    
    def __init__(
        self,
        detail: str = "Unauthorized",
        headers: Optional[Dict[str, Any]] = None,
        error_code: str = "UNAUTHORIZED",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class ForbiddenException(HTTPException):
    """Exception raised when access is forbidden"""
    
    def __init__(
        self,
        detail: str = "Forbidden",
        headers: Optional[Dict[str, Any]] = None,
        error_code: str = "FORBIDDEN",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class ConflictException(HTTPException):
    """Exception raised when there is a conflict"""
    
    def __init__(
        self,
        detail: str = "Resource conflict",
        headers: Optional[Dict[str, Any]] = None,
        error_code: str = "CONFLICT",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class BadRequestException(HTTPException):
    """Exception raised for bad requests"""
    
    def __init__(
        self,
        detail: str = "Bad request",
        headers: Optional[Dict[str, Any]] = None,
        error_code: str = "BAD_REQUEST",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class InternalServerException(HTTPException):
    """Exception raised for internal server errors"""
    
    def __init__(
        self,
        detail: str = "Internal server error",
        headers: Optional[Dict[str, Any]] = None,
        error_code: str = "INTERNAL_SERVER_ERROR",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle custom HTTP exceptions"""
    error_response = {
        "error": {
            "code": getattr(exc, "error_code", "HTTP_ERROR"),
            "message": exc.detail,
            "status_code": exc.status_code,
        }
    }
    
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    error_response = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": errors,
        }
    }
    
    logger.warning(
        f"Validation error: {errors}",
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response,
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    error_response = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Data validation failed",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": errors,
        }
    }
    
    logger.warning(
        f"Pydantic validation error: {errors}",
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response,
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    error_response = {
        "error": {
            "code": "DATABASE_ERROR",
            "message": "A database error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
    }
    
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


async def integrity_exception_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """Handle database integrity constraint violations"""
    error_message = "Database integrity constraint violated"
    
    if "unique constraint" in str(exc.orig).lower():
        error_message = "Resource already exists"
        status_code = status.HTTP_409_CONFLICT
        error_code = "DUPLICATE_RESOURCE"
    elif "foreign key constraint" in str(exc.orig).lower():
        error_message = "Referenced resource does not exist"
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "INVALID_REFERENCE"
    else:
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "INTEGRITY_ERROR"
    
    error_response = {
        "error": {
            "code": error_code,
            "message": error_message,
            "status_code": status_code,
        }
    }
    
    logger.warning(
        f"Integrity error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions"""
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
    }
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app"""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
```
```