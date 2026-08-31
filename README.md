# Karyam — Individual MVP

AI-powered manager dashboard: task tracking, timesheets, and an AI chatbot.

## Backend setup
1. Install PostgreSQL locally and make sure it's running.
2. Create the database and user:
```sql
   CREATE USER karyam_user WITH PASSWORD 'karyam_dev_pass';
   CREATE DATABASE karyam OWNER karyam_user;
```
3. cd into `backend/`, create a virtual environment, and install dependencies:
python -m venv venv source venv/bin/activate # on Windows: venv\Scripts\activate pip install -r requirements.txt
4. Copy `.env.example` to `.env` and adjust if needed.
5. Run the server:
uvicorn app.main:app --reload
6. Visit http://localhost:8000/health — you should see a status "ok" response.