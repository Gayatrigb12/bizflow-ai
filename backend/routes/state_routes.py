from flask import Blueprint, jsonify, current_app

from backend.auth.permissions import jwt_required, requires_roles
from backend.services.report_service import ReportService
from backend.storage.database import get_db_session
from backend.storage.repositories.activity_repository import ActivityRepository

state_bp = Blueprint('state_bp', __name__)


@state_bp.route('/api/state', methods=['GET'])
@jwt_required
def api_state():
    with get_db_session() as session:
        report_service = ReportService(session)
        base_state = report_service.build_dashboard_state()
        activity_repo = ActivityRepository(session)
        activity = [entry.to_dict() for entry in activity_repo.list_recent(50)]

    base_state['activity'] = activity
    return jsonify(base_state)


@state_bp.route('/api/reset', methods=['POST'])
@requires_roles('admin')
def api_reset():
    if current_app.config['ENV'] == 'production':
        return jsonify({'error': 'Reset is disabled in production'}), 403

    from backend.storage.models import Base
    from backend.storage.database import engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return jsonify({'ok': True})
