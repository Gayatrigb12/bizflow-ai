from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.storage.models import PendingAction


class PendingActionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, pending_action: PendingAction) -> PendingAction:
        self.session.add(pending_action)
        self.session.flush()
        return pending_action

    def get_by_id(self, pending_action_id: int) -> Optional[PendingAction]:
        return self.session.get(PendingAction, pending_action_id)

    def list_pending(self, limit: int = 50) -> List[PendingAction]:
        result = self.session.execute(
            select(PendingAction).where(PendingAction.status == 'pending').order_by(PendingAction.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    def save(self, pending_action: PendingAction) -> PendingAction:
        self.session.add(pending_action)
        self.session.flush()
        return pending_action
