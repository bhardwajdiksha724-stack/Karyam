"""
Seeds realistic demo data into your running Karyam backend.

Run this AFTER your backend is up (uvicorn app.main:app --reload) and you
already have your own manager account. It logs in as you, creates a few
demo employees, a spread of tasks, and some timesheet entries — so your
dashboard looks like a real, lived-in app instead of an empty shell.

Usage:
    python seed_demo_data.py
"""

from datetime import date, timedelta

import requests

BASE_URL = "http://localhost:8000"

DEMO_EMPLOYEES = [
    {"name": "Priya Sharma", "email": "priya@karyam.ai", "role": "Designer", "team": "Design"},
    {"name": "Rohan Verma", "email": "rohan@karyam.ai", "role": "Developer", "team": "Engineering"},
    {"name": "Ananya Iyer", "email": "ananya@karyam.ai", "role": "QA Engineer", "team": "Engineering"},
]
DEMO_PASSWORD = "demo1234"


def main():
    print("Karyam demo data seeder\n")
    manager_email = input("Your manager login email:  ").strip()
    manager_password = input("Your manager login password: ").strip()

    # --- log in as the manager ---
    resp = requests.post(
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
        resp = requests.post(
            f"{BASE_URL}/auth/signup",
            json={**emp, "password": DEMO_PASSWORD},
        )
        if resp.status_code == 200:
            employee_ids[emp["name"]] = resp.json()["id"]
            print(f"Created employee: {emp['name']}")
        elif resp.status_code == 400:
            print(f"Employee already exists, skipping: {emp['name']}")
            # Look up their id via the employee list so we can still assign tasks to them
            emp_list = requests.get(f"{BASE_URL}/employees", headers=headers).json()
            match = next((e for e in emp_list if e["email"] == emp["email"]), None)
            if match:
                employee_ids[emp["name"]] = match["id"]
        else:
            print(f"Unexpected error creating {emp['name']}: {resp.status_code} {resp.text}")

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
        resp = requests.post(f"{BASE_URL}/tasks", json=payload, headers=headers)
        if resp.status_code == 200:
            task_ids.append(resp.json()["id"])
            print(f"Created task: {t['title']}")
        else:
            print(f"Failed to create task '{t['title']}': {resp.status_code} {resp.text}")

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
            resp = requests.post(f"{BASE_URL}/timesheets", json=payload, headers=headers)
            if resp.status_code == 200:
                # approve roughly half of them so the demo shows both states
                if day_offset % 2 == 0:
                    entry_id = resp.json()["id"]
                    requests.patch(
                        f"{BASE_URL}/timesheets/{entry_id}",
                        json={"approved": True},
                        headers=headers,
                    )
            else:
                print(f"Failed to log timesheet entry: {resp.status_code} {resp.text}")

    print("\nDone! Refresh your dashboard — you should now see a populated team, task board, and timesheets.")
    print(f"(Demo employee login password, if you want to test as one of them: {DEMO_PASSWORD})")


if __name__ == "__main__":
    main()