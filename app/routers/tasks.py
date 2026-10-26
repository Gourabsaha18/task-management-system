
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Task, User
from app.schemas import TaskCreate, TaskResponse, TaskUpdate


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


# CREATE: Add a new task
@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task_data: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = Task(
        **task_data.model_dump(),
        owner_id=current_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


# READ: Get all tasks belonging to the logged-in user
@router.get("/", response_model=list[TaskResponse])
def get_tasks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    task_status: Annotated[
        str | None,
        Query(alias="status", pattern="^(pending|in_progress|completed)$"),
    ] = None,
    priority: Annotated[
        str | None,
        Query(pattern="^(low|medium|high)$"),
    ] = None,
):
    query = select(Task).where(Task.owner_id == current_user.id)

    if task_status is not None:
        query = query.where(Task.status == task_status)

    if priority is not None:
        query = query.where(Task.priority == priority)

    query = query.order_by(Task.created_at.desc())

    return list(db.scalars(query).all())


# READ: Get one task by its ID
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.owner_id == current_user.id,
        )
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


# UPDATE: Edit an existing task
@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.owner_id == current_user.id,
        )
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    updates = task_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


# DELETE: Remove a task
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.owner_id == current_user.id,
        )
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    db.delete(task)
    db.commit()

    return None
