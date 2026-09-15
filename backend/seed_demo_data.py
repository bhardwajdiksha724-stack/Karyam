"""
Seeds realistic demo data into your running Karyam backend.

Run this AFTER your backend is up and you already have your own manager
account. It logs in as you, creates a few demo employees, a spread of tasks,
and some timesheet entries — so your dashboard looks like a real, lived-in
app instead of an empty shell.

This version automatically retries requests that get dropped — common on
free-tier hosting where a tiny CPU allocation can make bcrypt password
hashing slow enough to trigger a connection reset.

Usage:
    python seed_demo_data.py
"""

import time
from datetime import date, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://karyam-backend-5v1t.onrender.com"

DEMO_EMPLOYEES = [
    {"name": "Priya Sharma", "email": "priya@karyam.ai", "role": "Designer", "team": "Design"},
    {"name": "Rohan Verma", "email": "rohan@karyam.ai", "role": "Developer", "team": "Engineering"},
    {"name": "Ananya Iyer", "email": "ananya@karyam.ai", "role": "QA Engineer", "team": "Engineering"},
]
DEMO_PASSWORD = "demo1234"

# Small pause between requests so we don't hammer a tiny free-tier instance.
REQUEST_DELAY_SECONDS = 1.5


def make_resilient_session() -> requests.Session:
    """A requests Session that automatically retries dropped connections
    with increasing delays — handles Render free-tier hiccups gracefully."""
    session = requests.Session()
    retry_strategy = Retry(
        total=6,
        backoff_factor=3,  # waits 3s, 6s, 12s, 24s... between retries
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET", "POST", "PATCH", "DELETE"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def main():
    print("Karyam demo data seeder\n")
    print("(Using automatic retries — if your backend is on a free-tier host,")
    print("this may take a bit longer than usual, that's expected.)\n")

    session = make_resilient_session()

    manager_email = input("Your manager login email: ").strip()
    manager_password = input("Your manager login password: ").strip()

    # --- log in as the manager ---
    resp = session.post(
        f"{BASE_URL}/auth/login",
        json={"email": manager_email, "password": manager_password},
    )
    if resp.status_code != 200:
        print(f"\nLogin failed: {resp.status_code} {resp.text}")
        print("Double-check your email/password and that the backend is running.")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in.\n")

    # --- create demo employees (skip any that already exist) ---
    employee_ids = {}
    for emp in DEMO_EMPLOYEES:
        resp = session.post(
            f"{BASE_URL}/auth/signup",
            json={**emp, "password": DEMO_PASSWORD},
        )
        if resp.status_code == 200:
            employee_ids[emp["name"]] = resp.json()["id"]
            print(f"Created employee: {emp['name']}")
        elif resp.status_code == 400:
            print(f"Employee already exists, skipping: {emp['name']}")
            emp_list = session.get(f"{BASE_URL}/employees", headers=headers).json()
            match = next((e for e in emp_list if e["email"] == emp["email"]), None)
            if match:
                employee_ids[emp["name"]] = match["id"]
        else:
            print(f"Unexpected error creating {emp['name']}: {resp.status_code} {resp.text}")
        time.sleep(REQUEST_DELAY_SECONDS)

    if not employee_ids:
        print("\nNo employees available to assign tasks to — stopping.")
        return

    names = list(employee_ids.keys())
    today = date.today()

    # --- create a spread of tasks across all three columns ---
    demo_tasks = [
        {"title": "Design new onboarding flow", "priority": "high", "status": "todo",
         "due_date": str(today + timedelta(days=5)), "assignee": names[0 % len(names)]},
        {"title": "Fix login page responsiveness", "priority": "medium", "status": "todo",
         "due_date": str(today - timedelta(days=2)), "assignee": names[1 % len(names)]},  # overdue on purpose
        {"title": "Write API integration tests", "priority": "medium", "status": "in_progress",
         "due_date": str(today + timedelta(days=3)), "assignee": names[2 % len(names)]},
        {"title": "Review pull request #42", "priority": "low", "status": "in_progress",
         "due_date": None, "assignee": names[1 % len(names)]},
        {"title": "Set up CI pipeline", "priority": "high", "status": "in_progress",
         "due_date": str(today + timedelta(days=1)), "assignee": names[1 % len(names)]},
        {"title": "Update design system docs", "priority": "low", "status": "done",
         "due_date": None, "assignee": names[0 % len(names)]},
        {"title": "Fix timezone bug in timesheets", "priority": "high", "status": "done",
         "due_date": None, "assignee": names[2 % len(names)]},
        {"title": "Draft Q3 sprint plan", "priority": "medium", "status": "todo",
         "due_date": str(today + timedelta(days=7)), "assignee": names[0 % len(names)]},
    ]

    task_ids = []
    for t in demo_tasks:
        payload = {
            "title": t["title"],
            "priority": t["priority"],
            "status": t["status"],
            "due_date": t["due_date"],
            "assignee_id": employee_ids[t["assignee"]],
        }
        resp = session.post(f"{BASE_URL}/tasks", json=payload, headers=headers)
        if resp.status_code == 200:
            task_ids.append(resp.json()["id"])
            print(f"Created task: {t['title']}")
        else:
            print(f"Failed to create task '{t['title']}': {resp.status_code} {resp.text}")
        time.sleep(REQUEST_DELAY_SECONDS)

    # --- log some timesheet entries for this week ---
    for i, name in enumerate(names):
        for day_offset in range(3):
            entry_date = today - timedelta(days=day_offset)
            payload = {
                "employee_id": employee_ids[name],
                "task_id": task_ids[i % len(task_ids)] if task_ids else None,
                "entry_date": str(entry_date),
                "hours": 4 + day_offset,
            }
            resp = session.post(f"{BASE_URL}/timesheets", json=payload, headers=headers)
            if resp.status_code == 200:
                if day_offset % 2 == 0:
                    entry_id = resp.json()["id"]
                    session.patch(
                        f"{BASE_URL}/timesheets/{entry_id}",
                        json={"approved": True},
                        headers=headers,
                    )
            else:
                print(f"Failed to log timesheet entry: {resp.status_code} {resp.text}")
            time.sleep(REQUEST_DELAY_SECONDS)

    print("\nDone! Refresh your dashboard — you should now see a populated team, task board, and timesheets.")
    print(f"(Demo employee login password, if you want to test as one of them: {DEMO_PASSWORD})")


if __name__ == "__main__":
    main()