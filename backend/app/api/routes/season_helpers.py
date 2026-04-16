from sqlmodel import select

from app.models import Season, UserSeasonProgress


def update_user_task_progress(session, user_id: int, task_type: str):
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
        from app.models import UserSeasonProgress

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
