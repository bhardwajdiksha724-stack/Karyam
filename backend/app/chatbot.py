import json
import os
from dataclasses import dataclass
from datetime import date
from typing import Optional

from groq import Groq
from sqlmodel import Session, select

from app.agent_tools import TOOLS, ToolError, propose_actions
from app.models import Employee, Task, TimesheetEntry
from app.rag import retrieve_relevant_chunks

MODEL = "openai/gpt-oss-120b"

_groq_client = None


@dataclass
class ChatResult:
    """What the chat endpoints return: always a reply, and optionally a
    proposed action waiting for the user's confirmation."""
    reply: str
    action_token: Optional[str] = None
    action_summaries: Optional[list[str]] = None


def get_groq_client() -> Groq:
    """Lazily creates the Groq client so a missing API key doesn't crash the
    whole app on startup — only when someone actually uses the chatbot."""
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file — see .env.example."
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def build_context(session: Session) -> str:
    """Pulls the current state of tasks, timesheets, and employees out of
    Postgres and turns it into a compact text summary. This is the ONLY data
    the chatbot sees — it never touches the database directly, and the LLM
    never sees raw SQL or table structure, just this summary. Ids are included
    so that when Kai takes an action it can refer to the exact task or person."""
    employees = session.exec(select(Employee)).all()
    tasks = session.exec(select(Task)).all()
    timesheets = session.exec(select(TimesheetEntry)).all()

    today = date.today()
    lines = ["TEAM:"]
    for emp in employees:
        emp_tasks = [t for t in tasks if t.assignee_id == emp.id]
        open_tasks = [t for t in emp_tasks if t.status != "done"]
        overdue = [t for t in open_tasks if t.due_date and t.due_date < today]
        lines.append(
            f"- {emp.name} (id {emp.id}, {emp.role}, {emp.team}): "
            f"{len(open_tasks)} open task(s), {len(overdue)} overdue"
        )

    lines.append("\nTASKS:")
    if not tasks:
        lines.append("- No tasks exist yet.")
    for t in tasks:
        assignee = next((e.name for e in employees if e.id == t.assignee_id), "Unassigned")
        due = f", due {t.due_date}" if t.due_date else ""
        overdue_flag = " [OVERDUE]" if t.due_date and t.due_date < today and t.status != "done" else ""
        lines.append(
            f"- [task id {t.id}] \"{t.title}\" — assigned to {assignee}, priority {t.priority.value}, "
            f"status {t.status.value}{due}{overdue_flag}"
        )

    lines.append("\nTIMESHEETS (all logged entries):")
    if not timesheets:
        lines.append("- No timesheet entries exist yet.")
    total_hours_by_employee = {}
    for ts in timesheets:
        emp_name = next((e.name for e in employees if e.id == ts.employee_id), "Unknown")
        total_hours_by_employee[emp_name] = total_hours_by_employee.get(emp_name, 0) + ts.hours
    for name, hours in total_hours_by_employee.items():
        lines.append(f"- {name}: {hours} total hours logged")

    return "\n".join(lines)


SYSTEM_PROMPT = """You are Kai, Karyam's AI assistant for a team task and \
timesheet dashboard. Answer questions using ONLY the data provided below \
— never make up tasks, people, or numbers that aren't in it. If the data \
doesn't contain what's needed to answer, say so plainly. Keep answers \
concise and conversational, not a data dump.

The data includes a line telling you who is currently asking ("CURRENT USER"). \
When the question uses "my", "I", or "me", it refers to that specific person \
— answer about their tasks/hours specifically, not the whole team, unless \
they clearly ask about the team as a whole.

You can also DO things for the user with the tools provided: create a task, \
move a task to a new status, and log hours. Rules for using them:
- Only call a tool when the user clearly asks you to do something. A question \
gets a normal answer, not a tool call.
- Use the ids shown in the data (like "id 3" or "task id 7"). Never invent an \
id. If you can't tell which task or person they mean, ask a short question \
instead of guessing.
- The data includes TODAY's date. Work out relative dates like "tomorrow" or \
"Friday" from it and pass them as YYYY-MM-DD.
- Every action is shown to the user for confirmation before it happens, so \
never say it's already done. Just call the tool.
- If they ask for several things, call the tool once per thing."""


def ask_chatbot(question: str, session: Session, current_employee: Employee) -> ChatResult:
    today = date.today()
    context = (
        f"TODAY: {today.isoformat()} ({today.strftime('%A')})\n"
        f"CURRENT USER: {current_employee.name} "
        f"({current_employee.role}, {current_employee.team}) — "
        f"access level: {current_employee.access_role.value}\n\n"
        + build_context(session)
    )
    client = get_groq_client()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"DATA:\n{context}\n\nQUESTION: {question}"},
        ],
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.3,
        max_tokens=1024,
    )
    message = response.choices[0].message

    # The model asked to DO something. Validate it, then hand it to the user to confirm.
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        calls = []
        for tc in tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append({"tool": tc.function.name, "args": args})
        try:
            summaries, token = propose_actions(calls, session, current_employee)
        except ToolError as e:
            return ChatResult(reply=f"I can't do that: {e}")
        return ChatResult(
            reply="Here's what I'll do. Confirm and I'll go ahead:",
            action_token=token,
            action_summaries=summaries,
        )

    content = message.content
    if not content:
        content = "Sorry, I couldn't generate a response to that. Try rephrasing the question."
    return ChatResult(reply=content)


PUBLIC_SYSTEM_PROMPT = """You are Kai, Karyam's assistant on the login page, \
talking to a visitor who hasn't signed up yet — NOT a logged-in user.

Answer using ONLY the documentation excerpts provided below — these were \
retrieved specifically because they're relevant to the question. If the \
excerpts don't contain what's needed to answer, say so honestly rather than \
guessing, and suggest the visitor sign up to explore further.

You have NO access to any actual account data, tasks, or users — only the \
product documentation. Keep answers short, friendly, and conversational."""


def ask_public_chatbot(question: str) -> str:
    relevant_chunks = retrieve_relevant_chunks(question, top_k=2)

    if relevant_chunks:
        docs_text = "\n\n---\n\n".join(c["text"] for c in relevant_chunks)
    else:
        docs_text = "(No matching documentation found for this question.)"

    client = get_groq_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PUBLIC_SYSTEM_PROMPT},
            {"role": "user", "content": f"RETRIEVED DOCUMENTATION:\n{docs_text}\n\nQUESTION: {question}"},
        ],
        temperature=0.4,
        max_tokens=512,
    )
    content = response.choices[0].message.content
    if not content:
        content = "Sorry, I couldn't generate a response to that. Try rephrasing the question."
    return content