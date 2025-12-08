# ============================================
# BotFactory AI - Knowledge Base API
# ============================================

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_user, get_user_bot, DBSession, CurrentUser
from src.core.logging import api_logger
from src.models.bot import Bot
from src.models.knowledge import KnowledgeBase as KnowledgeModel, KnowledgeSourceType
from src.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeFAQCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
    KnowledgeList,
    KnowledgeListResponse,
    KnowledgeSearch,
    KnowledgeSearchResult,
    KnowledgeSearchResponse,
    KnowledgeStats,
)
from src.schemas.common import SuccessResponse, DeleteResponse

router = APIRouter(prefix="/bots/{bot_id}/knowledge", tags=["Knowledge Base"])


@router.get("", response_model=KnowledgeListResponse)
async def list_knowledge(
    bot_id: int,
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    source_type: Optional[KnowledgeSourceType] = None,
    is_active: Optional[bool] = None,
):
    """
    Bot bilimlar bazasi ro'yxatini olish.
    """
    # Verify bot ownership
    bot = await get_user_bot(bot_id, current_user, db)

    # Build query
    query = select(KnowledgeModel).where(
        KnowledgeModel.bot_id == bot_id,
        KnowledgeModel.parent_id.is_(None),  # Only top-level items
    )

    if source_type:
        query = query.where(KnowledgeModel.source_type == source_type)
    if is_active is not None:
        query = query.where(KnowledgeModel.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(KnowledgeModel.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    # Transform to list items with content preview
    knowledge_items = []
    for item in items:
        list_item = KnowledgeList(
            id=item.id,
            title=item.title,
            source_type=item.source_type,
            is_active=item.is_active,
            hit_count=item.hit_count,
            content_preview=item.content[:100] + "..." if len(item.content) > 100 else item.content,
            created_at=item.created_at,
        )
        knowledge_items.append(list_item)

    return KnowledgeListResponse(
        items=knowledge_items,
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    bot_id: int,
    knowledge_data: KnowledgeCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Yangi bilim qo'shish (matn).
    """
    bot = await get_user_bot(bot_id, current_user, db)

    knowledge = KnowledgeModel(
        bot_id=bot_id,
        title=knowledge_data.title,
        content=knowledge_data.content,
        source_type=knowledge_data.source_type,
        source_url=knowledge_data.source_url,
    )

    db.add(knowledge)
    await db.commit()
    await db.refresh(knowledge)

    api_logger.info(f"Knowledge created: {knowledge.title} for bot {bot.name}")

    return knowledge


@router.post("/faq", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    bot_id: int,
    faq_data: KnowledgeFAQCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Yangi FAQ (savol-javob) qo'shish.
    """
    bot = await get_user_bot(bot_id, current_user, db)

    knowledge = KnowledgeModel(
        bot_id=bot_id,
        title=faq_data.question[:100],  # Use question as title
        content=f"Savol: {faq_data.question}\nJavob: {faq_data.answer}",
        source_type=KnowledgeSourceType.FAQ,
        question=faq_data.question,
        answer=faq_data.answer,
    )

    db.add(knowledge)
    await db.commit()
    await db.refresh(knowledge)

    api_logger.info(f"FAQ created for bot {bot.name}")

    return knowledge


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    bot_id: int,
    knowledge_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bilim elementini olish.
    """
    bot = await get_user_bot(bot_id, current_user, db)

    result = await db.execute(
        select(KnowledgeModel).where(
            KnowledgeModel.id == knowledge_id,
            KnowledgeModel.bot_id == bot_id,
        )
    )
    knowledge = result.scalar_one_or_none()

    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bilim elementi topilmadi",
        )

    return knowledge


@router.patch("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    bot_id: int,
    knowledge_id: int,
    knowledge_data: KnowledgeUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bilim elementini yangilash.
    """
    bot = await get_user_bot(bot_id, current_user, db)

    result = await db.execute(
        select(KnowledgeModel).where(
            KnowledgeModel.id == knowledge_id,
            KnowledgeModel.bot_id == bot_id,
        )
    )
    knowledge = result.scalar_one_or_none()

    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bilim elementi topilmadi",
        )

    update_data = knowledge_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(knowledge, field, value)

    knowledge.updated_at = datetime.utcnow()
    # Clear embedding to re-generate
    knowledge.embedding = None
    
    await db.commit()
    await db.refresh(knowledge)

    return knowledge


@router.delete("/{knowledge_id}", response_model=DeleteResponse)
async def delete_knowledge(
    bot_id: int,
    knowledge_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bilim elementini o'chirish.
    """
    bot = await get_user_bot(bot_id, current_user, db)

    result = await db.execute(
        select(KnowledgeModel).where(
            KnowledgeModel.id == knowledge_id,
            KnowledgeModel.bot_id == bot_id,
        )
    )
    knowledge = result.scalar_one_or_none()

    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bilim elementi topilmadi",
        )

    await db.delete(knowledge)
    await db.commit()

    api_logger.info(f"Knowledge deleted: ID {knowledge_id} from bot {bot.name}")

    return DeleteResponse(id=knowledge_id)


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    bot_id: int,
    search_query: KnowledgeSearch,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bilimlar bazasidan qidirish (semantic search).
    """
    bot = await get_user_bot(bot_id, current_user, db)

    # TODO: Implement actual semantic search with embeddings
    # For now, use simple text search
    query = select(KnowledgeModel).where(
        KnowledgeModel.bot_id == bot_id,
        KnowledgeModel.is_active == True,
        KnowledgeModel.content.ilike(f"%{search_query.query}%"),
    ).limit(search_query.limit)

    if search_query.source_types:
        query = query.where(KnowledgeModel.source_type.in_(search_query.source_types))

    result = await db.execute(query)
    items = result.scalars().all()

    results = [
        KnowledgeSearchResult(
            id=item.id,
            title=item.title,
            content=item.content[:500],
            source_type=item.source_type,
            score=1.0,  # Placeholder score
        )
        for item in items
    ]

    return KnowledgeSearchResponse(
        results=results,
        query=search_query.query,
        total_found=len(results),
    )


@router.get("/stats", response_model=KnowledgeStats)
async def get_knowledge_stats(
    bot_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bilimlar bazasi statistikasi.
    """
    bot = await get_user_bot(bot_id, current_user, db)

    # Get counts by type
    result = await db.execute(
        select(
            KnowledgeModel.source_type,
            func.count(KnowledgeModel.id),
        )
        .where(KnowledgeModel.bot_id == bot_id)
        .group_by(KnowledgeModel.source_type)
    )
    type_counts = {row[0].value: row[1] for row in result.all()}

    # Get total and active counts
    total_result = await db.execute(
        select(func.count()).where(KnowledgeModel.bot_id == bot_id)
    )
    total = total_result.scalar() or 0

    active_result = await db.execute(
        select(func.count()).where(
            KnowledgeModel.bot_id == bot_id,
            KnowledgeModel.is_active == True,
        )
    )
    active = active_result.scalar() or 0

    # Get total hits
    hits_result = await db.execute(
        select(func.sum(KnowledgeModel.hit_count)).where(KnowledgeModel.bot_id == bot_id)
    )
    total_hits = hits_result.scalar() or 0

    # Get most used items
    most_used_result = await db.execute(
        select(KnowledgeModel)
        .where(KnowledgeModel.bot_id == bot_id)
        .order_by(KnowledgeModel.hit_count.desc())
        .limit(5)
    )
    most_used = most_used_result.scalars().all()

    return KnowledgeStats(
        total_items=total,
        active_items=active,
        by_type=type_counts,
        total_hits=total_hits,
        most_used=[
            KnowledgeList(
                id=item.id,
                title=item.title,
                source_type=item.source_type,
                is_active=item.is_active,
                hit_count=item.hit_count,
                content_preview=item.content[:100],
                created_at=item.created_at,
            )
            for item in most_used
        ],
    )
