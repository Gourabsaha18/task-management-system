# Task Management System

A RESTful task management API built with Python, FastAPI, SQLAlchemy, and SQLite.

## Planned features
- User registration and login
- Password hashing and JWT authentication
- Create, read, update, and delete tasks
- Per-user task ownership
- Input validation and consistent error handling
- Interactive API documentation with Swagger UI
- Automated tests

## Project structure
See the `app/` package for application code and `tests/` for automated tests.

## Setup (Windows PowerShell)
1. Create and activate a virtual environment:
   ```powershell
   py -3.11 -m venv task_env
   .\task_env\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
3. Configure `.env` with a strong, private `SECRET_KEY`.
4. Run the API (after the implementation steps are complete):
   ```powershell
   uvicorn app.main:app --reload
   ```
5. Open `http://127.0.0.1:8000/docs`.

> This ZIP provides the initial project structure and starter files. The API implementation will be added step by step.
