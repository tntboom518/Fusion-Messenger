import json
from datetime import datetime, timedelta, timezone
from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, func, select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    User,
    Season,
    SeasonTask,
    UserSeasonProgress,
    SeasonPublic,
    SeasonTaskPublic,
    UserSeasonProgressPublic,
    Message,
)

router = APIRouter(prefix="/seasons", tags=["seasons"])


class CreateSeason(BaseModel):
    name: str
    number: int = Field(ge=1)


class CreateTask(BaseModel):
    name: str
    description: str | None = None
    target_count: int = Field(ge=1)
    task_type: str
    base_reward: int = Field(ge=0)


class StartSeason(BaseModel):
    season_id: int


class SeasonTaskWithProgress(BaseModel):
    id: int
    name: str
    description: str | None
    target_count: int
    task_type: str
    base_reward: int
    current_progress: int = 0
    is_completed: bool = False


@router.get("/", response_model=list[SeasonPublic])
def get_seasons(session: SessionDep) -> Any:
    """Получить все сезоны"""
    seasons = session.exec(select(Season).order_by(Season.number.desc())).all()
    return seasons


@router.get("/active", response_model=SeasonPublic | None)
def get_active_season(session: SessionDep) -> Any:
    """Получить активный сезон"""
    season = session.exec(select(Season).where(Season.is_active == True)).first()
    return season


@router.get("/{season_id}/tasks", response_model=list[SeasonTaskWithProgress])
def get_season_tasks(
    season_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Получить задания сезона с прогрессом пользователя"""
    tasks = session.exec(
        select(SeasonTask).where(SeasonTask.season_id == season_id)
    ).all()

    season = session.exec(select(Season).where(Season.id == season_id)).first()
    if not season:
        return []

    progress = session.exec(
        select(UserSeasonProgress).where(
            UserSeasonProgress.user_id == current_user.id,
            UserSeasonProgress.season_id == season_id,
        )
    ).first()

    if not progress:
        progress = UserSeasonProgress(
            user_id=current_user.id,
            season_id=season_id,
            progress=0,
            completed_tasks="[]",
            total_reward_earned=0,
            messages_sent=0,
            chats_created=0,
            friends_added=0,
            media_shared=0,
        )
        session.add(progress)
        session.commit()
        session.refresh(progress)

    completed = (
        json.loads(progress.completed_tasks) if progress.completed_tasks != "[]" else []
    )

    result = []
    for task in tasks:
        current = 0
        if task.task_type == "messages":
            current = progress.messages_sent
        elif task.task_type == "chats":
            current = progress.chats_created
        elif task.task_type == "friends":
            current = progress.friends_added
        elif task.task_type == "media":
            current = progress.media_shared

        result.append(
            SeasonTaskWithProgress(
                id=task.id,
                name=task.name,
                description=task.description,
                target_count=task.target_count,
                task_type=task.task_type,
                base_reward=task.base_reward,
                current_progress=current,
                is_completed=task.id in completed,
            )
        )

    return result


@router.get("/my-progress")
def get_my_progress(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Получить прогресс текущего сезона"""
    season = session.exec(select(Season).where(Season.is_active == True)).first()
    if not season:
        return None

    progress = session.exec(
        select(UserSeasonProgress).where(
            UserSeasonProgress.user_id == current_user.id,
            UserSeasonProgress.season_id == season.id,
        )
    ).first()

    if not progress:
        progress = UserSeasonProgress(
            user_id=current_user.id,
            season_id=season.id,
            progress=0,
            completed_tasks="[]",
            total_reward_earned=0,
            messages_sent=0,
            chats_created=0,
            friends_added=0,
            media_shared=0,
        )
        session.add(progress)
        session.commit()
        session.refresh(progress)

    return {
        "id": progress.id,
        "season_id": progress.season_id,
        "progress": progress.progress,
        "completed_tasks": json.loads(progress.completed_tasks)
        if progress.completed_tasks != "[]"
        else [],
        "total_reward_earned": progress.total_reward_earned,
    }


@router.post("/claim-task")
def claim_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_data: dict,
) -> Any:
    """Проверить выполнение задания и выдать награду"""
    task_id = task_data.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id required")

    season = session.exec(select(Season).where(Season.is_active == True)).first()
    if not season:
        raise HTTPException(status_code=400, detail="No active season")

    task = session.get(SeasonTask, task_id)
    if not task or task.season_id != season.id:
        raise HTTPException(status_code=404, detail="Task not found")

    progress = session.exec(
        select(UserSeasonProgress).where(
            UserSeasonProgress.user_id == current_user.id,
            UserSeasonProgress.season_id == season.id,
        )
    ).first()

    if not progress:
        progress = UserSeasonProgress(
            user_id=current_user.id,
            season_id=season.id,
            progress=0,
            completed_tasks="[]",
            total_reward_earned=0,
            messages_sent=0,
            chats_created=0,
            friends_added=0,
            media_shared=0,
        )
        session.add(progress)
        session.commit()
        session.refresh(progress)

    current = 0
    if task.task_type == "messages":
        current = progress.messages_sent
    elif task.task_type == "chats":
        current = progress.chats_created
    elif task.task_type == "friends":
        current = progress.friends_added
    elif task.task_type == "media":
        current = progress.media_shared

    completed = (
        json.loads(progress.completed_tasks) if progress.completed_tasks != "[]" else []
    )

    if task.id in completed:
        raise HTTPException(status_code=400, detail="Task already completed")

    if current < task.target_count:
        raise HTTPException(
            status_code=400,
            detail=f"Task not completed yet. Progress: {current}/{task.target_count}",
        )

    reward = task.base_reward
    bonus = (progress.progress * task.base_reward) // 100
    total_reward = reward + bonus

    current_user.balance += total_reward

    # Даём 2 часа Ultra за выполнение задания
    now = datetime.now(timezone.utc)
    if (
        current_user.is_ultra
        and current_user.ultra_expires_at
        and current_user.ultra_expires_at > now
    ):
        current_user.ultra_expires_at = current_user.ultra_expires_at + timedelta(
            hours=2
        )
    else:
        current_user.is_ultra = True
        current_user.ultra_expires_at = now + timedelta(hours=2)

    completed.append(task.id)
    progress.completed_tasks = json.dumps(completed)
    progress.progress += 1
    progress.total_reward_earned += total_reward

    session.add(current_user)
    session.add(progress)
    session.commit()
    session.refresh(progress)

    return {
        "id": progress.id,
        "season_id": progress.season_id,
        "progress": progress.progress,
        "completed_tasks": completed,
        "total_reward_earned": progress.total_reward_earned,
    }


def update_user_task_progress(session: Session, user_id: int, task_type: str):
    """Обновить прогресс пользователя по типу задания"""
    season = session.exec(select(Season).where(Season.is_active == True)).first()
    if not season:
        return

    progress = session.exec(
        select(UserSeasonProgress).where(
            UserSeasonProgress.user_id == user_id,
            UserSeasonProgress.season_id == season.id,
        )
    ).first()

    if not progress:
        progress = UserSeasonProgress(
            user_id=user_id,
            season_id=season.id,
            progress=0,
            completed_tasks="[]",
            total_reward_earned=0,
            messages_sent=0,
            chats_created=0,
            friends_added=0,
            media_shared=0,
        )
        session.add(progress)

    if task_type == "messages":
        progress.messages_sent += 1
    elif task_type == "chats":
        progress.chats_created += 1
    elif task_type == "friends":
        progress.friends_added += 1
    elif task_type == "media":
        progress.media_shared += 1

    session.add(progress)
    session.commit()


@router.post(
    "/admin/create",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=SeasonPublic,
)
def create_season(
    session: SessionDep,
    season_data: CreateSeason,
) -> Any:
    """Создать сезон (админ)"""
    existing = session.exec(
        select(Season).where(Season.number == season_data.number)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Season number already exists")

    season = Season(name=season_data.name, number=season_data.number, is_active=False)
    session.add(season)
    session.commit()
    session.refresh(season)
    return season


@router.post(
    "/admin/{season_id}/tasks",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=SeasonTaskPublic,
)
def create_task(
    season_id: int,
    session: SessionDep,
    task_data: CreateTask,
) -> Any:
    """Создать задание (админ)"""
    season = session.get(Season, season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    task = SeasonTask(
        season_id=season_id,
        name=task_data.name,
        description=task_data.description,
        target_count=task_data.target_count,
        task_type=task_data.task_type,
        base_reward=task_data.base_reward,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.post(
    "/admin/start",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=SeasonPublic,
)
def start_season(
    session: SessionDep,
    start_data: StartSeason,
) -> Any:
    """Начать сезон (админ)"""
    season = session.get(Season, start_data.season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    active_season = session.exec(select(Season).where(Season.is_active == True)).first()
    if active_season:
        active_season.is_active = False
        session.add(active_season)

    season.is_active = True
    session.add(season)
    session.commit()
    session.refresh(season)

    return season


@router.post(
    "/admin/end",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def end_season(session: SessionDep) -> Message:
    """Завершить текущий сезон (админ)"""
    season = session.exec(select(Season).where(Season.is_active == True)).first()
    if not season:
        raise HTTPException(status_code=400, detail="No active season")

    season.is_active = False
    session.add(season)
    session.commit()

    return Message(message=f"Season {season.name} ended")
