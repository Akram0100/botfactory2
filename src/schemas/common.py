# ============================================
# BotFactory AI - Common Schemas
# ============================================

from typing import Generic, TypeVar, List, Optional, Any

from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    page: int = 1
    size: int = 20
    pages: int = 1

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int = 1,
        size: int = 20,
    ) -> "PaginatedResponse[T]":
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str = "Muvaffaqiyatli bajarildi"


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
    redis: str = "connected"


class DeleteResponse(BaseModel):
    """Delete operation response."""
    deleted: bool = True
    id: int


class CountResponse(BaseModel):
    """Count response."""
    count: int


class IDResponse(BaseModel):
    """ID response."""
    id: int


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# ===========================================
# Query Parameters
# ===========================================

class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class SortParams(BaseModel):
    """Sort query parameters."""
    sort_by: str = "created_at"
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class DateRangeParams(BaseModel):
    """Date range query parameters."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
