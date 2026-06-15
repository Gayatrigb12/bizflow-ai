from flask import Blueprint, jsonify

from backend.auth.permissions import requires_roles
from backend.services.analytics_service import AnalyticsService
from backend.storage.database import get_db_session

analytics_bp = Blueprint('analytics_bp', __name__)


@analytics_bp.route('/api/analytics/summary', methods=['GET'])
@requires_roles('manager', 'admin')
def api_analytics_summary():
    with get_db_session() as session:
        analytics_summary = AnalyticsService(session).build_analytics_report()
    return jsonify(analytics_summary)
