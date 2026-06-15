from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.storage.models import ChatMessage

VALID_CONTEXTS = {'inventory', 'orders', 'customers', 'general'}


class ChatMessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(
        self,
        user_prompt: str,
        ai_response: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        actor: Optional[str] = None,
        context_type: str = 'general',
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
    ) -> ChatMessage:
        normalized_context = context_type if context_type in VALID_CONTEXTS else 'general'
        chat_message = ChatMessage(
            user_prompt=user_prompt,
            ai_response=ai_response,
            session_id=session_id,
            metadata_json=metadata,
            actor=actor,
            context_type=normalized_context,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self.session.add(chat_message)
        self.session.flush()
        return chat_message

    def list_recent(
        self,
        limit: int = 30,
        session_id: Optional[str] = None,
    ) -> List[ChatMessage]:
        stmt = select(ChatMessage)
        if session_id:
            stmt = stmt.where(ChatMessage.session_id == session_id)
        stmt = stmt.order_by(ChatMessage.created_at.desc()).limit(limit)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
