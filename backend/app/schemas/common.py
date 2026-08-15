"""
Common/shared Pydantic schemas used across multiple domains.
"""
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list response."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """Simple success message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Standard error response shape."""
    detail: str
    error_code: str | None = None
