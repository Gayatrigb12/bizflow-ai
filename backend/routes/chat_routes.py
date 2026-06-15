# import traceback

# from flask import Blueprint, jsonify, request, current_app

# from backend.auth.permissions import requires_roles
# from backend.services.chat_service import ChatService
# from backend.storage.database import get_db_session

# chat_bp = Blueprint('chat_bp', __name__)


# @chat_bp.route('/api/chat', methods=['POST'])
# @requires_roles('staff', 'manager', 'admin')
# def api_chat():
#     payload = request.get_json(silent=True) or {}
#     message = str(payload.get('message') or '').strip()
#     if not message:
#         return jsonify({'error': 'Message is required'}), 400

#     groq_key = current_app.config.get('GROQ_API_KEY')
#     if not groq_key or groq_key == 'gsk_your_key_here':
#         return jsonify({'error': 'Groq API key not configured', 'details': 'Set GROQ_API_KEY in .env'}), 500

#     with get_db_session() as session:
#         chat_service = ChatService(session)
#         try:
#             response = chat_service.process_message(message)
#         # except Exception as exc:
#         #     return jsonify({'error': 'Chat processing failed', 'details': str(exc)}), 500
#         except Exception as exc:
#             traceback.print_exc()

#     return jsonify({
#         'error': 'Chat processing failed',
#         'details': str(exc)
#     }), 500
#     return jsonify(response)



import traceback

from flask import Blueprint, jsonify, request, current_app

from backend.auth.permissions import requires_roles
from backend.services.chat_service import ChatService
from backend.storage.database import get_db_session

chat_bp = Blueprint('chat_bp', __name__)


@chat_bp.route('/api/chat', methods=['POST'])
@requires_roles('staff', 'manager', 'admin')
def api_chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get('message') or '').strip()

    if not message:
        return jsonify({
            'error': 'Message is required'
        }), 400

    groq_key = current_app.config.get('GROQ_API_KEY')

    if not groq_key or groq_key == 'gsk_your_key_here':
        return jsonify({
            'error': 'Groq API key not configured',
            'details': 'Set GROQ_API_KEY in .env'
        }), 500

    with get_db_session() as session:
        chat_service = ChatService(session)

        try:
            response = chat_service.process_message(message)

            return jsonify(response)

        except Exception as exc:
            # Print full traceback in terminal
            traceback.print_exc()

            # Return error details in API response
            return jsonify({
                'error': 'Chat processing failed',
                'details': str(exc)
            }), 500

        

        