# ============================================
# BotFactory AI - Knowledge Base Schemas
# ============================================

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field, HttpUrl

from src.models.knowledge import KnowledgeSourceType


# ===========================================
# Request Schemas
# ===========================================

class KnowledgeCreate(BaseModel):
    """Schema for creating knowledge base item."""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    source_type: KnowledgeSourceType = KnowledgeSourceType.TEXT
    source_url: Optional[str] = Field(None, max_length=500)


class KnowledgeFAQCreate(BaseModel):
    """Schema for creating FAQ item."""
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=5)


class KnowledgeProductCreate(BaseModel):
    """Schema for creating product knowledge."""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeURLCreate(BaseModel):
    """Schema for importing from URL."""
    url: str = Field(..., max_length=500)
    title: Optional[str] = Field(None, max_length=255)


class KnowledgeUpdate(BaseModel):
    """Schema for updating knowledge base item."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None


class KnowledgeBulkCreate(BaseModel):
    """Schema for bulk creating knowledge items."""
    items: List[KnowledgeCreate]


# ===========================================
# Response Schemas
# ===========================================

class KnowledgeBase(BaseModel):
    """Base knowledge schema."""
    id: int
    title: str
    source_type: KnowledgeSourceType
    is_active: bool
    hit_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeResponse(KnowledgeBase):
    """Full knowledge response schema."""
    bot_id: int
    content: str
    source_url: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    metadata: dict[str, Any]
    chunk_index: int
    total_chunks: int
    updated_at: datetime


class KnowledgeList(BaseModel):
    """Knowledge list item."""
    id: int
    title: str
    source_type: KnowledgeSourceType
    is_active: bool
    hit_count: int
    content_preview: str  # First 100 chars
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeListResponse(BaseModel):
    """Paginated knowledge list response."""
    items: List[KnowledgeList]
    total: int
    page: int
    size: int


class KnowledgeStats(BaseModel):
    """Knowledge base statistics."""
    total_items: int
    active_items: int
    by_type: dict[str, int]
    total_hits: int
    most_used: List[KnowledgeList]


# ===========================================
# Search Schemas
# ===========================================

class KnowledgeSearch(BaseModel):
    """Knowledge search query."""
    query: str = Field(..., min_length=2, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)
    source_types: Optional[List[KnowledgeSourceType]] = None


class KnowledgeSearchResult(BaseModel):
    """Search result item."""
    id: int
    title: str
    content: str
    source_type: KnowledgeSourceType
    score: float  # Similarity score


class KnowledgeSearchResponse(BaseModel):
    """Search results."""
    results: List[KnowledgeSearchResult]
    query: str
    total_found: int
