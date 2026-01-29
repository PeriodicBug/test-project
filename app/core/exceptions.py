# app/core/exceptions.py
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException as FastAPIHTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger(__name__)


class HTTPException(FastAPIHTTPException):
    """Base HTTP exception with enhanced error details"""
    
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or f"ERR_{status_code}"


class NotFoundException(HTTPException):
    """Exception raised when a resource is not found"""
    
    def __init__(
        self,
        detail: str = "Resource not found",
        resource: Optional[str] = None,
        resource_id: Optional[Union[str, int]] = None,
    ) -> None:
        error_detail = detail
        if resource and resource_id:
            error_detail = f"{resource} with id '{resource_id}' not found"
        elif resource:
            error_detail = f"{resource} not found"
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_detail,
            error_code="NOT_FOUND",
        )
        self.resource = resource
        self.resource_id = resource_id


class ValidationException(HTTPException):
    """Exception raised when validation fails"""
    
    def __init__(
        self,
        detail: Union[str, Dict[str, Any]] = "Validation error",
        errors: Optional[list] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
        )
        self.errors = errors or []


class UnauthorizedException(HTTPException):
    """Exception raised when authentication fails"""
    
    def __init__(
        self,
        detail: str = "Authentication required",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    """Exception raised when user lacks permissions"""
    
    def __init__(
        self,
        detail: str = "Insufficient permissions",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
        )


class ConflictException(HTTPException):
    """Exception raised when there's a conflict with existing data"""
    
    def __init__(
        self,
        detail: str = "Resource conflict",
        resource: Optional[str] = None,
    ) -> None:
        error_detail = detail
        if resource:
            error_detail = f"Conflict with existing {resource}"
        
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_detail,
            error_code="CONFLICT",
        )


class BadRequestException(HTTPException):
    """Exception raised for bad requests"""
    
    def __init__(
        self,
        detail: str = "Bad request",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BAD_REQUEST",
        )


class InternalServerException(HTTPException):
    """Exception raised for internal server errors"""
    
    def __init__(
        self,
        detail: str = "Internal server error",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="INTERNAL_SERVER_ERROR",
        )


class DatabaseException(HTTPException):
    """Exception raised for database errors"""
    
    def __init__(
        self,
        detail: str = "Database error occurred",
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR",
        )
        self.original_error = original_error


def create_error_response(
    status_code: int,
    detail: Any,
    error_code: Optional[str] = None,
    errors: Optional[list] = None,
) -> Dict[str, Any]:
    """Create standardized error response"""
    response = {
        "success": False,
        "error": {
            "code": error_code or f"ERR_{status_code}",
            "message": detail,
        }
    }
    
    if errors:
        response["error"]["details"] = errors
    
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Global handler for HTTP exceptions"""
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_code": getattr(exc, "error_code", None),
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            detail=exc.detail,
            error_code=getattr(exc, "error_code", None),
            errors=getattr(exc, "errors", None),
        ),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Global handler for validation exceptions"""
    errors = []
    
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
    else:
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
    
    logger.warning(
        f"Validation error on {request.url.path}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation failed",
            error_code="VALIDATION_ERROR",
            errors=errors,
        ),
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Global handler for SQLAlchemy exceptions"""
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )
    
    if isinstance(exc, IntegrityError):
        detail = "Database integrity constraint violated"
        error_code = "INTEGRITY_ERROR"
        status_code = status.HTTP_409_CONFLICT
    else:
        detail = "Database operation failed"
        error_code = "DATABASE_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return JSONResponse(
        status_code=status_code,
        content=create_error_response(
            status_code=status_code,
            detail=detail,
            error_code=error_code,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global handler for unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
            error_code="INTERNAL_SERVER_ERROR",
        ),
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app"""
    from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
    
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
    app.add_exception_handler(FastAPIRequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)