from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from sqlmodel import Session, select
from DormShareAPI.application.Data.models import Chat, Message, User, UserRole
from DormShareAPI.application.Services.Auth import SECRET_KEY, ALGORITHM
import jwt
import uuid



def get_user_from_token(token: str, session: Session) -> type[User] | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            return None
        return session.get(User, user_id)
    except:
        return None



async def chat_handler(websocket: WebSocket, chat_id: str, token: str, session: Session, manager):
    await websocket.accept()

    user = get_user_from_token(token, session)
    if not user:
        await websocket.close(code=4001)
        return

    chat = session.get(Chat, chat_id)
    if not chat:
        await websocket.close(code=4004)
        return

    if user.id not in (chat.lender_id, chat.borrower_id) and user.role != UserRole.ADMIN:
        await websocket.close(code=4003)
        return

    await manager.connect(websocket, chat_id)

    history = session.exec(
        select(Message)
        .where(Message.chat_id == uuid.UUID(chat_id))
        .order_by(Message.timestamp)
    ).all()

    await websocket.send_json({
        "type": "history",
        "messages": [
            {
                "id": str(m.id),
                "content": m.content,
                "sender_id": str(m.sender_id),
                "timestamp": m.timestamp.isoformat(),
                "is_viewed": m.is_viewed,
                "reaction": m.reaction
            }
            for m in history
        ]
    })

    try:
        while True:
            data = await websocket.receive_json()

            message = Message(
                content=data["content"],
                sender_id=user.id,
                chat_id=uuid.UUID(chat_id)
            )
            session.add(message)
            session.commit()
            session.refresh(message)

            await manager.broadcast_to_chat(chat_id, {
                "type": "message",
                "id": str(message.id),
                "content": message.content,
                "sender_id": str(message.sender_id),
                "timestamp": message.timestamp.isoformat(),
                "is_viewed": message.is_viewed,
                "reaction": message.reaction
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)