from flask import Blueprint, jsonify, request, current_app, g

from backend.auth.permissions import requires_roles
from backend.services.chat_service import ChatService
from backend.storage.database import get_db_session
from backend.routes.error_utils import error_response, bad_request
from backend.storage.repositories.chat_message_repository import VALID_CONTEXTS

chat_bp = Blueprint('chat_bp', __name__)


@chat_bp.route('/api/chat', methods=['POST'])
@requires_roles('staff', 'manager', 'admin')
def api_chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get('message') or '').strip()

    if not message:
        return bad_request('Message is required')

    # Module/context tagging: inventory, orders, customers, general
    context_type = str(payload.get('context') or 'general').strip().lower()
    if context_type not in VALID_CONTEXTS:
        context_type = 'general'
    context_id = payload.get('context_id')
    try:
        context_id = int(context_id) if context_id is not None else None
    except (TypeError, ValueError):
        context_id = None

    groq_key = current_app.config.get('GROQ_API_KEY')
    if not groq_key or groq_key == 'gsk_your_key_here':
        return jsonify({
            'error': 'Groq API key not configured',
            'details': 'Set GROQ_API_KEY in .env'
        }), 500

    actor = (getattr(g, 'current_user', {}) or {}).get('username', 'unknown')

    try:
        with get_db_session() as session:
            chat_service = ChatService(session)
            response = chat_service.process_message(
                message,
                context_type=context_type,
                context_id=context_id,
                actor=actor,
            )
        return jsonify(response)
    except ValueError as exc:
        return bad_request(str(exc))
    except Exception as exc:
        return error_response(exc, 'Chat processing failed')


@chat_bp.route('/api/chat/history', methods=['GET'])
@requires_roles('staff', 'manager', 'admin')
def api_chat_history():
    context_type = str(request.args.get('context') or 'general').strip().lower()
    if context_type not in VALID_CONTEXTS:
        context_type = 'general'
    context_id = request.args.get('context_id')
    try:
        context_id = int(context_id) if context_id is not None else None
    except (TypeError, ValueError):
        context_id = None

    try:
        with get_db_session() as session:
            from backend.storage.repositories.chat_message_repository import ChatMessageRepository
            messages = ChatMessageRepository(session).list_by_context(context_type, context_id)
            result = [m.to_dict() for m in messages]
        return jsonify(result)
    except Exception as exc:
        return error_response(exc, 'Failed to load chat history')
