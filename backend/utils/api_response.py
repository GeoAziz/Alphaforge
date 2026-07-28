"""
Standard API response format for consistent error/success handling.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from fastapi import HTTPException


class ApiResponse:
    """Standardized API response wrapper."""

    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> Dict[str, Any]:
        """Return standardized success response."""
        return {
            "success": True,
            "status_code": status_code,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def error(message: str, status_code: int = 400, errors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return standardized error response."""
        return {
            "success": False,
            "status_code": status_code,
            "message": message,
            "errors": errors or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def validation_error(field_errors: Dict[str, str]) -> Dict[str, Any]:
        """Return validation error response."""
        return ApiResponse.error(
            message="Validation failed",
            status_code=422,
            errors=field_errors
        )

    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> Dict[str, Any]:
        """Return 401 unauthorized response."""
        return ApiResponse.error(message, status_code=401)

    @staticmethod
    def forbidden(message: str = "Forbidden") -> Dict[str, Any]:
        """Return 403 forbidden response."""
        return ApiResponse.error(message, status_code=403)

    @staticmethod
    def not_found(message: str = "Not found") -> Dict[str, Any]:
        """Return 404 not found response."""
        return ApiResponse.error(message, status_code=404)

    @staticmethod
    def server_error(message: str = "Internal server error") -> Dict[str, Any]:
        """Return 500 server error response."""
        return ApiResponse.error(message, status_code=500)
