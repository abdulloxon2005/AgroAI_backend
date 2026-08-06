"""
AgroAI — WebSocket Endpoints
Real-time chat and scan via WebSocket connections.
"""
import json
import uuid as uuid_mod

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.db.database import get_db as get_session
from app.services.chat_service import ChatService

logger = structlog.get_logger()

router = APIRouter()


async def authenticate_ws(websocket: WebSocket) -> str | None:
    """Authenticate WebSocket connection via token. Returns user_id string (UUID)."""
    token = websocket.query_params.get("token")
    if not token:
        try:
            auth_message = await websocket.receive_text()
            auth_data = json.loads(auth_message)
            token = auth_data.get("token")
        except Exception:
            return None

    if not token:
        return None

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # Validate it's a valid UUID string
    try:
        uuid_mod.UUID(user_id)
    except (ValueError, TypeError):
        return None

    return user_id


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    user_id = await authenticate_ws(websocket)
    if user_id is None:
        await websocket.send_json({"type": "error", "message": "Avtorizatsiya xatosi"})
        await websocket.close(code=4001)
        return

    await websocket.send_json({"type": "connected", "message": "Ulanish muvaffaqiyatli"})

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            msg_type = message_data.get("type", "chat")

            async for db in get_session():
                try:
                    if msg_type == "chat":
                        session_id = message_data.get("session_id")
                        content = message_data.get("message", "")

                        if not session_id or not content:
                            await websocket.send_json({
                                "type": "error",
                                "message": "session_id va message talab qilinadi",
                            })
                            continue

                        service = ChatService(db)
                        result = await service.send_message(session_id, user_id, content)

                        last_msg = result.messages[-1] if result.messages else None

                        await websocket.send_json({
                            "type": "chat_response",
                            "session_id": session_id,
                            "message": {
                                "id": str(last_msg.id) if last_msg else "",
                                "role": "assistant",
                                "content": last_msg.content if last_msg else "",
                                "created_at": last_msg.created_at.isoformat() if last_msg else "",
                            },
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Noma'lum xabar turi: {msg_type}",
                        })

                except Exception as e:
                    logger.exception("ws_message_error", error=str(e))
                    await websocket.send_json({
                        "type": "error",
                        "message": "Xatolik yuz berdi",
                    })

    except WebSocketDisconnect:
        logger.info("ws_client_disconnected", user_id=user_id)
    except Exception as e:
        logger.exception("ws_error", error=str(e))
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
