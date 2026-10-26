# TaskFlow frontend (React + Tailwind CSS)

Responsive dashboard based on the supplied screenshot. It connects to your existing FastAPI + SQLAlchemy + SQLite + JWT backend and does not replace it.

## Setup
1. Copy this `frontend` folder into the root of your existing `task-management-system` folder, alongside `app/` and `tests/`.
2. Install Node.js 18+ (Node 20 LTS recommended).
3. In PowerShell:
   ```powershell
   cd frontend
   Copy-Item .env.example .env
   npm install
   npm run dev
   ```
   Open the Vite URL, usually http://localhost:5173.
4. In a separate terminal, from your backend project root, activate `task_env` and run:
   ```powershell
   python -m uvicorn app.main:app --reload
   ```
   Swagger: http://127.0.0.1:8000/docs

## CORS
If not already enabled, add this import to `app/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware
```
After creating `app = FastAPI(...)`, add:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Keep your existing routers, lifespan, and tests. Restart FastAPI and run `python -m pytest -v`.

## API contract
- `POST /auth/register`: JSON username/email/password
- `POST /auth/login`: URL-encoded `username` (email) and `password`, returns `access_token`
- `GET /tasks/`, `POST /tasks/`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}`
- Task statuses: `pending`, `in_progress`, `completed`; priorities: `low`, `medium`, `high`.
- Configure `VITE_API_URL` in `frontend/.env` if your backend URL differs from `http://127.0.0.1:8000`.

## Included
Login/register, JWT bearer header, task CRUD, status board, list view, search, priority filter, due-date calendar, upcoming tasks, responsive sidebar, dark appearance, loading/error/empty/success states.

The token is stored in `localStorage` for a straightforward portfolio demo. Never commit `.env` files or backend secrets. For production, consider secure HttpOnly cookies and a suitable refresh-token strategy.
