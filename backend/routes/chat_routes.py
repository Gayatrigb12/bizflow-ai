import logging
import traceback

from flask import Blueprint, current_app, g, jsonify, request

from backend.auth.permissions import requires_roles
from backend.routes.error_utils import structured_error
from backend.services.chat_service import ChatService
from backend.storage.database import get_db_session
from backend.storage.repositories.chat_message_repository import ChatMessageRepository

chat_bp = Blueprint('chat_bp', __name__)
logger = logging.getLogger('bizflow')


def _current_actor() -> str:
    current_user = getattr(g, 'current_user', {}) or {}
    return str(current_user.get('sub') or current_user.get('username') or 'user')


@chat_bp.route('/api/chat/history', methods=['GET'])
@requires_roles('staff', 'manager', 'admin')
def api_chat_history():
    try:
        limit = min(int(request.args.get('limit', 30)), 100)
    except (TypeError, ValueError):
        return structured_error('Invalid limit parameter', code=400)

    session_id = request.args.get('session_id') or None

    with get_db_session() as session:
        repo = ChatMessageRepository(session)
        messages = repo.list_recent(limit=limit, session_id=session_id)
        return jsonify([msg.to_dict() for msg in messages])


@chat_bp.route('/api/chat', methods=['POST'])
@requires_roles('staff', 'manager', 'admin')
def api_chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get('message') or '').strip()
    session_id = str(payload.get('session_id') or '').strip() or None

    if not message:
        return structured_error('Message is required', code=400)

    groq_key = current_app.config.get('GROQ_API_KEY')
    if not groq_key or groq_key == 'gsk_your_key_here':
        return structured_error(
            'Groq API key not configured',
            code=500,
            details='Set GROQ_API_KEY in .env',
        )

    with get_db_session() as session:
        chat_service = ChatService(session)
        try:
            response = chat_service.process_message(
                message,
                session_id=session_id,
                actor=_current_actor(),
            )
            return jsonify(response)
        except ValueError as exc:
            return structured_error(str(exc), code=400)
        except Exception as exc:
            logger.error('Chat processing failed: %s\n%s', exc, traceback.format_exc())
            return structured_error(
                'Chat processing failed',
                code=500,
                details=str(exc),
            )
