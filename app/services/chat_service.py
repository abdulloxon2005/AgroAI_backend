from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.models import ChatSession, ChatMessage
from app.core.exceptions import NotFoundException, ForbiddenException
from app.core.config import settings
import google.generativeai as genai

genai.configure(api_key=settings.GEMINI_API_KEY)


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def create_session(self, user_id: int) -> ChatSession:
        session = ChatSession(user_id=user_id, title="Yangi suhbat")
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session, attribute_names=["messages"])
        return session

    async def get_user_sessions(self, user_id: int) -> list:
        result = await self.db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        sessions = result.scalars().all()

        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.messages),
            }
            for s in sessions
        ]

    async def get_session(self, session_id: int, user_id: int) -> ChatSession:
        result = await self.db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundException("Suhbat topilmadi")
        if session.user_id != user_id:
            raise ForbiddenException("Bu suhbatga ruxsat yo'q")

        return session

    async def send_message(
        self, session_id: int, user_id: int, message: str
    ) -> ChatSession:
        session = await self.get_session(session_id, user_id)

        # Save user message
        user_msg = ChatMessage(session_id=session_id, role="user", content=message)
        self.db.add(user_msg)

        # Build conversation history for AgroAI
        history_parts = []
        for m in session.messages:
            role = "Foydalanuvchi" if m.role == "user" else "AgroAI Agronom"
            history_parts.append(f"{role}: {m.content}")
        history_parts.append(f"Foydalanuvchi: {message}")

        system_prompt = """Sen AgroAI — qishloq xo'jaligi, ekinlar va botanika bo'yicha sun'iy intellekt agronom maslahatchisisan.
        O'zingni har doim AgroAI deb ataysan. Faqat qishloq xo'jaligi, o'simliklar, kasalliklar, tuproq, ob-havo va fermerlik bilan bog'liq
        savollarga professional javob ber. Javoblarni o'zbek tilida ber."""

        full_prompt = f"{system_prompt}\n\nSuhbat tarixi:\n" + "\n".join(history_parts)

        try:
            response = await self.model.generate_content_async(full_prompt)
            ai_response = response.text
        except Exception:
            ai_response = "Kechirasiz, hozirda javob berishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."

        # Save AI response
        ai_msg = ChatMessage(
            session_id=session_id, role="assistant", content=ai_response
        )
        self.db.add(ai_msg)
        await self.db.flush()

        # Update session title if first message
        if len(session.messages) <= 2:
            try:
                title_response = await self.model.generate_content_async(
                    f"Quyidagi suhbatga 5 so'zdan iborat sarlavha ber. Faqat sarlavhani yoz, boshqa hech narsa yozma:\n{message}"
                )
                session.title = title_response.text.strip()[:100]
            except Exception:
                pass

        await self.db.refresh(session, attribute_names=["messages"])
        return session

    async def delete_session(self, session_id: int, user_id: int):
        session = await self.get_session(session_id, user_id)
        await self.db.delete(session)
