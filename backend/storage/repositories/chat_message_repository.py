from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.storage.models import ChatMessage

VALID_CONTEXTS = {'inventory', 'orders', 'customers', 'general'}


class ChatMessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(
        self,
        context_type: str,
        role: str,
        message: str,
        context_id: Optional[int] = None,
        actions: Optional[list] = None,
        actor: Optional[str] = None,
    ) -> ChatMessage:
        normalized_context = context_type if context_type in VALID_CONTEXTS else 'general'
        chat_message = ChatMessage(
            context_type=normalized_context,
            context_id=context_id,
            role=role,
            message=message,
            actions=actions,
            actor=actor,
        )
        self.session.add(chat_message)
        self.session.flush()
        return chat_message

    def list_by_context(self, context_type: str, context_id: Optional[int] = None, limit: int = 50) -> List[ChatMessage]:
        normalized_context = context_type if context_type in VALID_CONTEXTS else 'general'
        stmt = select(ChatMessage).where(ChatMessage.context_type == normalized_context)
        if context_id is not None:
            stmt = stmt.where(ChatMessage.context_id == context_id)
        stmt = stmt.order_by(ChatMessage.created_at.asc()).limit(limit)
        result = self.session.execute(stmt)
        return result.scalars().all()
