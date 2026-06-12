from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.storage.models import ActivityLog


class ActivityRepository:
    def __init__(self, session: Session):
        self.session = session

    def log(self, action_type: str, description: str, actor: str | None = None) -> ActivityLog:
        activity = ActivityLog(action_type=action_type, description=description, actor=actor)
        self.session.add(activity)
        self.session.flush()
        return activity

    def list_recent(self, limit: int = 50) -> List[ActivityLog]:
        result = self.session.execute(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit))
        return result.scalars().all()
