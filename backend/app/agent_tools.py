"""
Actions Kai can take on a user's behalf ("agentic" Kai).

How it works:
1. The LLM is given a list of tools (create a task, move a task, log hours).
   When the user asks Kai to DO something, the model replies with a
   structured tool call instead of text.
2. We never run that call straight away. We validate it against the user's
   real permissions, show a plain-English summary, and wait for a click on
   Confirm.
3. The confirmation is a short-lived SIGNED token holding the exact
   validated actions, so what the user approved is exactly what runs. On
   confirm we validate again (permissions can change in 5 minutes), then
   execute.

Permissions are enforced HERE, on the server, never by trusting the model or
the browser. An employee asking Kai to create a task gets the same
"managers only" answer they'd get from the API itself.
"""

import secrets
import time
from datetime import date, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from sqlmodel import Session

from app.auth import ALGORITHM, SECRET_KEY
from app.models import AccessRole, Employee, Task, TaskPriority, TaskStatus, TimesheetEntry

ACTION_TOKEN_TTL_MINUTES = 5
MAX_ACTIONS_PER_REQUEST = 5
STATUS_LABELS = {"todo": "To Do", "in_progress": "In Progress", "done": "Done"}

# token id -> expiry timestamp. Stops one confirmation being applied twice
# (for example a double click). Fine for a single server process.
_used_token_ids: dict[str, float] = {}


class ToolError(Exception):
    """A problem the user can understand and act on (permission, bad id, bad input)."""


# The tool definitions the LLM sees (OpenAI-style function calling, which
# Groq supports).
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task on the board. Managers only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short task title"},
                    "description": {"type": "string", "description": "Optional longer description"},
                    "assignee_id": {
                        "type": "integer",
                        "description": "Employee id to assign it to, taken from the data. Omit if unassigned.",
                    },
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "due_date": {"type": "string", "description": "Due date as YYYY-MM-DD"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task_status",
            "description": (
                "Move an existing task to a new status. Managers can move any task; "
                "employees can only move tasks assigned to them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "Task id, taken from the data"},
                    "status": {"type": "string", "enum": ["todo", "in_progress", "done"]},
                },
                "required": ["task_id", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_hours",
            "description": (
                "Log worked hours on the timesheet. Employees can only log for themselves; "
                "managers can log for anyone."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hours": {"type": "number", "description": "Hours worked, between 0 and 24"},
                    "entry_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."},
                    "task_id": {"type": "integer", "description": "Optional task the hours were spent on"},
                    "employee_id": {
                        "type": "integer",
                        "description": "Who the hours are for. Defaults to the current user.",
                    },
                },
                "required": ["hours"],
            },
        },
    },
]


# ---------- small helpers ----------

def _is_manager(me: Employee) -> bool:
    return me.access_role == AccessRole.manager


def _to_int(value: Any, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ToolError(f"I need a valid {label}.")


def _to_date(value: Any):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ToolError(f"'{value}' isn't a date I can use. I need it as YYYY-MM-DD.")


def _nice_date(d: date) -> str:
    return d.strftime("%a %d %b")


# ---------- validation: turns a raw model request into a safe, normalized action ----------

def _prepare(tool: str, args: dict, session: Session, me: Employee) -> tuple[dict, str]:
    """Validates one requested action against the user's permissions and the
    real data. Returns (clean_args, human_readable_summary) or raises ToolError."""
    if not isinstance(args, dict):
        args = {}

    if tool == "create_task":
        if not _is_manager(me):
            raise ToolError("Only managers can create tasks.")
        title = str(args.get("title") or "").strip()
        if not title:
            raise ToolError("I need a title for the task.")
        priority = args.get("priority") or "medium"
        if priority not in {p.value for p in TaskPriority}:
            raise ToolError("Priority has to be low, medium or high.")
        due = _to_date(args.get("due_date"))

        assignee_id = args.get("assignee_id")
        assignee = None
        if assignee_id is not None:
            assignee_id = _to_int(assignee_id, "assignee")
            assignee = session.get(Employee, assignee_id)
            if not assignee:
                raise ToolError(f"I couldn't find an employee with id {assignee_id}.")

        clean = {
            "title": title,
            "description": (str(args["description"]).strip() or None) if args.get("description") else None,
            "assignee_id": assignee_id,
            "priority": priority,
            "due_date": due.isoformat() if due else None,
        }
        summary = f'Create task "{title}" ({priority} priority)'
        if assignee:
            summary += f", assigned to {assignee.name}"
        if due:
            summary += f", due {_nice_date(due)}"
        return clean, summary

    if tool == "update_task_status":
        task = session.get(Task, _to_int(args.get("task_id"), "task id"))
        if not task:
            raise ToolError("I couldn't find that task.")
        status = args.get("status")
        if status not in STATUS_LABELS:
            raise ToolError("Status has to be To Do, In Progress or Done.")
        if not _is_manager(me) and task.assignee_id != me.id:
            raise ToolError("You can only change the status of tasks assigned to you.")
        clean = {"task_id": task.id, "status": status}
        return clean, f'Move "{task.title}" to {STATUS_LABELS[status]}'

    if tool == "log_hours":
        try:
            hours = float(args.get("hours"))
        except (TypeError, ValueError):
            raise ToolError("I need to know how many hours to log.")
        if not 0 < hours <= 24:
            raise ToolError("Hours need to be between 0 and 24.")
        entry_date = _to_date(args.get("entry_date")) or date.today()

        target = me
        if args.get("employee_id") is not None:
            target_id = _to_int(args.get("employee_id"), "employee")
            if target_id != me.id:
                if not _is_manager(me):
                    raise ToolError("You can only log hours for yourself.")
                target = session.get(Employee, target_id)
                if not target:
                    raise ToolError(f"I couldn't find an employee with id {target_id}.")

        task = None
        if args.get("task_id") is not None:
            task = session.get(Task, _to_int(args.get("task_id"), "task id"))
            if not task:
                raise ToolError("I couldn't find that task.")

        clean = {
            "hours": hours,
            "entry_date": entry_date.isoformat(),
            "employee_id": target.id,
            "task_id": task.id if task else None,
        }
        summary = f"Log {hours:g}h for {target.name} on {_nice_date(entry_date)}"
        if task:
            summary += f' (task: "{task.title}")'
        return clean, summary

    raise ToolError("I don't know how to do that yet.")


# ---------- execution: the only place that writes to the database ----------

def _perform(tool: str, args: dict, session: Session) -> str:
    if tool == "create_task":
        task = Task(
            title=args["title"],
            description=args.get("description"),
            assignee_id=args.get("assignee_id"),
            priority=TaskPriority(args["priority"]),
            status=TaskStatus.todo,
            due_date=_to_date(args.get("due_date")),
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        who = ""
        if task.assignee_id:
            assignee = session.get(Employee, task.assignee_id)
            who = f" for {assignee.name}" if assignee else ""
        return f'Created task "{task.title}"{who}'

    if tool == "update_task_status":
        task = session.get(Task, args["task_id"])
        task.status = TaskStatus(args["status"])
        session.add(task)
        session.commit()
        return f'Moved "{task.title}" to {STATUS_LABELS[args["status"]]}'

    if tool == "log_hours":
        entry = TimesheetEntry(
            employee_id=args["employee_id"],
            task_id=args.get("task_id"),
            entry_date=_to_date(args["entry_date"]),
            hours=args["hours"],
        )
        session.add(entry)
        session.commit()
        person = session.get(Employee, args["employee_id"])
        return f"Logged {args['hours']:g}h for {person.name} on {_nice_date(entry.entry_date)}"

    raise ToolError("I don't know how to do that yet.")


# ---------- the two public steps: propose, then execute after confirmation ----------

def propose_actions(calls: list[dict], session: Session, me: Employee) -> tuple[list[str], str]:
    """Validates the model's requested actions and returns
    (summaries to show the user, signed confirmation token). Nothing is
    written to the database at this stage."""
    if not calls:
        raise ToolError("I wasn't able to work out what to do.")
    if len(calls) > MAX_ACTIONS_PER_REQUEST:
        raise ToolError(f"Let's keep it to {MAX_ACTIONS_PER_REQUEST} actions at a time.")

    prepared, summaries = [], []
    for call in calls:
        clean, summary = _prepare(call.get("tool", ""), call.get("args", {}), session, me)
        prepared.append({"tool": call["tool"], "args": clean})
        summaries.append(summary)

    # Deliberately uses "uid" (not "sub") so this token can never be used as a login token.
    token = jwt.encode(
        {
            "uid": me.id,
            "typ": "kai_action",
            "jti": secrets.token_urlsafe(8),
            "actions": prepared,
            "exp": datetime.utcnow() + timedelta(minutes=ACTION_TOKEN_TTL_MINUTES),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return summaries, token


def execute_token(token: str, session: Session, me: Employee) -> tuple[list[str], bool]:
    """Runs the actions inside a confirmation token. Returns
    (one result line per action, whether a task was just completed)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise ToolError("That confirmation expired or isn't valid. Just ask me again.")

    if payload.get("typ") != "kai_action" or payload.get("uid") != me.id:
        raise ToolError("That confirmation isn't valid for your account.")

    now = time.time()
    for used_id, expires in list(_used_token_ids.items()):
        if expires < now:
            del _used_token_ids[used_id]
    jti = payload.get("jti")
    if not jti or jti in _used_token_ids:
        raise ToolError("That action was already carried out.")
    _used_token_ids[jti] = float(payload.get("exp", now + 300))

    results, completed_a_task = [], False
    for action in payload.get("actions", []):
        try:
            # Validate again right before writing: permissions or data may have changed.
            clean, _ = _prepare(action["tool"], action["args"], session, me)
            results.append(_perform(action["tool"], clean, session))
            if action["tool"] == "update_task_status" and clean["status"] == "done":
                completed_a_task = True
        except ToolError as e:
            results.append(f"Couldn't do that one: {e}")
    return results, completed_a_task