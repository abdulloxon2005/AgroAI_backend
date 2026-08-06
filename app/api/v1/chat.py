"""
AgroAI — Chat Endpoints
AI Agronom chat sessions and messages via Gemini.
"""
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.db.database import get_db
from app.db.models import User, ChatSession, ChatMessage
from app.domain.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionListResponse,
    ChatMessageListResponse,
)
from app.api.deps import get_current_user
from app.core.ai_client import generate_with_timeout, get_chat_model

router = APIRouter(prefix="/chat", tags=["AI Chat"])

# Maximum number of history messages sent as context to the AI
_MAX_CONTEXT_MESSAGES = 20


def _parse_uuid(val: Any) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Chat sessiya ID formati noto'g'ri. Iltimos, yangi suhbat boshlang."
        )


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_in: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new chat session."""
    session = ChatSession(user_id=current_user.id, title=session_in.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Paginated list of user's chat sessions."""
    skip = (page - 1) * limit
    result = await db.execute(
        select(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()

    count_result = await db.execute(
        select(func.count(ChatSession.id)).filter(
            ChatSession.user_id == current_user.id
        )
    )
    total = count_result.scalar() or 0

    return {"items": sessions, "total": total, "page": page, "limit": limit}


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: str,
    message_in: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send message to a session and get AI response."""
    session_uuid = _parse_uuid(session_id)

    # Verify session belongs to user
    result = await db.execute(
        select(ChatSession).filter(
            ChatSession.id == session_uuid,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat sessiya topilmadi")

    # Save user message
    user_msg = ChatMessage(
        session_id=session_uuid, content=message_in.content, role="user"
    )
    db.add(user_msg)

    # Get recent conversation history (limited)
    try:
        history_result = await db.execute(
            select(ChatMessage)
            .filter(ChatMessage.session_id == session_uuid)
            .order_by(ChatMessage.created_at.desc())
            .limit(_MAX_CONTEXT_MESSAGES)
        )
        history = history_result.scalars().all()

        # Build context
        context_parts = []
        for msg in reversed(history):
            role = "Fermer" if msg.role == "user" else "AI Agronom"
            context_parts.append(f"{role}: {msg.content}")
        context_parts.append(f"Fermer: {message_in.content}")

        prompt = "\n".join(context_parts)
        ai_text = await generate_with_timeout(get_chat_model(), prompt)
    except Exception:
        ai_text = (
            "Kechirasiz, sun'iy intellekt xizmati javob berishda biroz uzilishga uchradi. "
            "Sizning savolingiz: '" + message_in.content + "'. "
            "Qishloq xo'jaligi va ekinlar parvarishi bo'yicha savollaringiz bo'lsa qayta so'rashingiz mumkin."
        )

    # Save AI response
    ai_msg = ChatMessage(session_id=session_uuid, content=ai_text, role="assistant")
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    return ai_msg


@router.get("/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
async def get_messages(
    session_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages in session (paginated)."""
    session_uuid = _parse_uuid(session_id)
    skip = (page - 1) * limit

    # Verify session
    sess_result = await db.execute(
        select(ChatSession).filter(
            ChatSession.id == session_uuid,
            ChatSession.user_id == current_user.id,
        )
    )
    if not sess_result.scalars().first():
        raise HTTPException(status_code=404, detail="Sessiya topilmadi")

    result = await db.execute(
        select(ChatMessage)
        .filter(ChatMessage.session_id == session_uuid)
        .order_by(ChatMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    return {"items": messages}


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a chat session and all its messages."""
    session_uuid = _parse_uuid(session_id)
    result = await db.execute(
        select(ChatSession).filter(
            ChatSession.id == session_uuid,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessiya topilmadi")

    await db.delete(session)
    await db.commit()
    return None

