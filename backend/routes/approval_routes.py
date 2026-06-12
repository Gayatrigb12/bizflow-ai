from flask import Blueprint, jsonify, request

from backend.auth.permissions import requires_roles
from backend.services.pending_action_service import PendingActionService
from backend.storage.database import get_db_session

approval_bp = Blueprint('approval_bp', __name__)


@approval_bp.route('/api/ai/pending-actions', methods=['GET'])
@requires_roles('manager', 'admin')
def api_list_pending_actions():
    with get_db_session() as session:
        service = PendingActionService(session)
        pending = service.list_pending()
    return jsonify([item.to_dict() for item in pending])


@approval_bp.route('/api/ai/pending-actions/<int:action_id>/approve', methods=['POST'])
@requires_roles('manager', 'admin')
def api_approve_pending_action(action_id: int):
    payload = request.get_json(silent=True) or {}
    reviewer = str(payload.get('reviewer') or 'admin')
    comment = str(payload.get('comment') or '')
    with get_db_session() as session:
        service = PendingActionService(session)
        try:
            result = service.approve_pending_action(action_id, reviewer=reviewer, review_comment=comment)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 404
    return jsonify(result)


@approval_bp.route('/api/ai/pending-actions/<int:action_id>/reject', methods=['POST'])
@requires_roles('manager', 'admin')
def api_reject_pending_action(action_id: int):
    payload = request.get_json(silent=True) or {}
    reviewer = str(payload.get('reviewer') or 'admin')
    comment = str(payload.get('comment') or '')
    with get_db_session() as session:
        service = PendingActionService(session)
        try:
            pending = service.reject_pending_action(action_id, reviewer=reviewer, review_comment=comment)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 404
    return jsonify(pending.to_dict())
