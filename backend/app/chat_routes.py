from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.agent_tools import ToolError, execute_token
from app.auth import get_current_employee
from app.chatbot import ask_chatbot, ask_public_chatbot
from app.database import get_session
from app.models import Employee

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ConfirmRequest(BaseModel):
    action_token: str


class ChatResponse(BaseModel):
    reply: str
    # Set when Kai proposes an action that needs the user's confirmation.
    action_token: Optional[str] = None
    action_summaries: Optional[List[str]] = None
    # True when a confirmed action just completed a task (frontend fires confetti).
    celebrate: bool = False


@router.post("", response_model=ChatResponse)
def chat(
    data: ChatRequest,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    try:
        result = ask_chatbot(data.message, session, current_employee)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {e}")
    return ChatResponse(
        reply=result.reply,
        action_token=result.action_token,
        action_summaries=result.action_summaries,
    )


@router.post("/confirm", response_model=ChatResponse)
def confirm_action(
    data: ConfirmRequest,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """Runs the action(s) the user just approved. The token was signed by the
    server in /chat, so it can't be edited, and it's re-validated here."""
    try:
        results, celebrate = execute_token(data.action_token, session, current_employee)
    except ToolError as e:
        raise HTTPException(status_code=400, detail=str(e))

    lines = [
        f"- ⚠️ {r}" if r.startswith("Couldn't") else f"- ✅ {r}"
        for r in results
    ]
    return ChatResponse(reply="\n".join(lines), celebrate=celebrate)


@router.post("/public", response_model=ChatResponse)
def public_chat(data: ChatRequest):
    """No login required — this is the marketing/FAQ chatbot on the login
    page. It has no database access, only retrieval over Karyam's own
    documentation, so there's nothing sensitive it could ever leak."""
    try:
        reply = ask_public_chatbot(data.message)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {e}")
    return ChatResponse(reply=reply)