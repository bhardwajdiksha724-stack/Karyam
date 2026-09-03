import os
from datetime import date

from groq import Groq
from sqlmodel import Session, select

from app.models import Employee, Task, TimesheetEntry

_groq_client = None


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
    never sees raw SQL or table structure, just this summary."""
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
            f"- {emp.name} ({emp.role}, {emp.team}): "
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
            f"- \"{t.title}\" — assigned to {assignee}, priority {t.priority.value}, "
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


SYSTEM_PROMPT = """You are Karyam, an AI assistant for a manager using a team \
task and timesheet dashboard. Answer the manager's question using ONLY the \
data provided below — never make up tasks, people, or numbers that aren't in \
it. If the data doesn't contain what's needed to answer, say so plainly. Keep \
answers concise and conversational, not a data dump."""


def ask_chatbot(question: str, session: Session) -> str:
    context = build_context(session)
    client = get_groq_client()

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"DATA:\n{context}\n\nQUESTION: {question}"},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    content = response.choices[0].message.content
    if not content:
        content = "Sorry, I couldn't generate a response to that. Try rephrasing the question."
    return content