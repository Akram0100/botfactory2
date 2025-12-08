# ============================================
# BotFactory AI - Knowledge Base Model
# ============================================

from typing import TYPE_CHECKING, Optional, List
import enum

from sqlalchemy import String, Enum, Text, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.bot import Bot


class KnowledgeSourceType(str, enum.Enum):
    """Source type for knowledge base items."""
    TEXT = "text"           # Direct text input
    FILE = "file"           # Uploaded file (PDF, DOCX, TXT)
    URL = "url"             # Web page content
    FAQ = "faq"             # Question-answer pair
    PRODUCT = "product"     # Product information


class KnowledgeBase(Base):
    """Knowledge base model for bot training data."""

    __tablename__ = "knowledge_base"

    # Bot relationship
    bot_id: Mapped[int] = mapped_column(
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[KnowledgeSourceType] = mapped_column(
        Enum(KnowledgeSourceType), default=KnowledgeSourceType.TEXT
    )
    source_url: Mapped[Optional[str]] = mapped_column(String(500))

    # For FAQ type
    question: Mapped[Optional[str]] = mapped_column(Text)
    answer: Mapped[Optional[str]] = mapped_column(Text)

    # For PRODUCT type
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)

    # Embeddings for semantic search
    # Storing as JSON array since we're using PostgreSQL
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100))

    # Chunking info (for large documents)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, default=1)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("knowledge_base.id", ondelete="CASCADE")
    )

    # Statistics
    hit_count: Mapped[int] = mapped_column(default=0)  # How often this was used

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    bot: Mapped["Bot"] = relationship(back_populates="knowledge_items")
    chunks: Mapped[List["KnowledgeBase"]] = relationship(
        "KnowledgeBase",
        lazy="selectin",
        join_depth=1,
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, title='{self.title[:30]}...')>"
