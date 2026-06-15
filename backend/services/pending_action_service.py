from typing import Any, Dict, List

from backend.ai.action_executor import execute_actions
from backend.storage.models import PendingAction, utc_now
from backend.storage.repositories.pending_action_repository import PendingActionRepository
from backend.storage.repositories.activity_repository import ActivityRepository


class PendingActionService:
    def __init__(self, session):
        self.session = session
        self.repository = PendingActionRepository(session)
        self.activity_repository = ActivityRepository(session)

    def create_pending_action(self, actions: List[Dict[str, Any]], reply: str, requested_by: str = 'AI') -> PendingAction:
        pending_action = PendingAction(
            action_type='ai_batch',
            payload={'reply': reply, 'actions': actions},
            status='pending',
            requested_by=requested_by,
            created_at=utc_now(),
        )
        return self.repository.create(pending_action)

    def list_pending(self, limit: int = 50) -> List[PendingAction]:
        return self.repository.list_pending(limit=limit)

    def get_pending(self, action_id: int) -> PendingAction | None:
        return self.repository.get_by_id(action_id)

    def approve_pending_action(self, action_id: int, reviewer: str = 'admin', review_comment: str = '') -> Dict[str, Any]:
        pending_action = self.repository.get_by_id(action_id)
        if not pending_action or pending_action.status != 'pending':
            raise ValueError('Pending action not found or not pending')

        payload = pending_action.payload or {}
        actions = payload.get('actions', [])
        executed = execute_actions(self.session, actions, actor=reviewer)

        pending_action.status = 'executed'
        pending_action.reviewed_by = reviewer
        pending_action.review_comment = review_comment
        pending_action.reviewed_at = utc_now()
        self.repository.save(pending_action)
        self.activity_repository.log('ai', f"Approved and executed pending action {action_id}", reviewer)
        return {'executed': executed, 'pending_action_id': action_id}

    def reject_pending_action(self, action_id: int, reviewer: str = 'admin', review_comment: str = '') -> PendingAction:
        pending_action = self.repository.get_by_id(action_id)
        if not pending_action or pending_action.status != 'pending':
            raise ValueError('Pending action not found or not pending')

        pending_action.status = 'rejected'
        pending_action.reviewed_by = reviewer
        pending_action.review_comment = review_comment
        pending_action.reviewed_at = utc_now()
        self.repository.save(pending_action)
        self.activity_repository.log('ai', f"Rejected pending action {action_id}", reviewer)
        return pending_action
