from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from DormShareAPI.application.Data.models import User, Chat
from DormShareAPI.application.Services.Auth import get_current_user
from DormShareAPI.application.Data.DataBase import get_session
from DormShareAPI.application.Handlers.ChatHandler import CreateChat, getChatById, getUserChats, chatDelete, getNewMessages, sendMessage
from uuid import UUID
from DormShareAPI.application.Data.PydenticModels import ChatResponse, SendMessage
from datetime import datetime



router = APIRouter(prefix="/chat",
                   tags=["Chat"])


@router.post("/create/{item_id}", status_code=201)
async def create_chat(item_id: UUID, session: Session = Depends(get_session),
                      current_user: User = Depends(get_current_user)):

    return await CreateChat(item_id, session, current_user)


@router.get("/get/{chat_id}", status_code=200, response_model=ChatResponse)
async def get_chat_by_id(chat_id: UUID, session: Session = Depends(get_session),
                         current_user: User = Depends(get_current_user)):

    return await getChatById(chat_id, session, current_user)


@router.get("/mine", status_code=200, response_model=list[ChatResponse])
async def get_mine_chats(session: Session = Depends(get_session),
                         current_user: User = Depends(get_current_user)):

    return await getUserChats(session, current_user)

@router.delete("/delete/{chat_id}", status_code=204)
async def delete_chat(chat_id: UUID, session: Session = Depends(get_session),
                         current_user: User = Depends(get_current_user)):

    return await chatDelete(chat_id, session, current_user)


@router.get("/messages/{chat_id}")
async def get_new_messages(
    chat_id: UUID,
    after: datetime,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)):

    return await getNewMessages(chat_id, after, session, current_user)


@router.post("/messages/{chat_id}", status_code=201)
async def send_message(
    chat_id: UUID,
    data: SendMessage,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    return await sendMessage(chat_id, data, session, current_user)