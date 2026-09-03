from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_employee
from app.chatbot import ask_chatbot, ask_public_chatbot
from app.database import get_session
from app.models import Employee

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
def chat(
    data: ChatRequest,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    try:
        reply = ask_chatbot(data.message, session, current_employee)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {e}")
    return ChatResponse(reply=reply)


@router.post("/public", response_model=ChatResponse)
def public_chat(data: ChatRequest):
    """No login required — this is the marketing/FAQ chatbot on the login
    page. It has no database access at all, only knowledge of the product
    itself, so there's nothing sensitive it could leak."""
    try:
        reply = ask_public_chatbot(data.message)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {e}")
    return ChatResponse(reply=reply)