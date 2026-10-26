
"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import Base, engine
from app.routers.tasks import router as tasks_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables when the application starts."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Task Management System API",
    description="A RESTful API for managing personal tasks.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow requests from the React/Vite frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers.
app.include_router(users_router)
app.include_router(tasks_router)


@app.get("/")
def home():
    """Display the API welcome message."""
    return {
        "message": "Task Management System API is running!"
    }


@app.get("/health")
def health_check():
    """Check whether the API is healthy."""
    return {"status": "healthy"}
