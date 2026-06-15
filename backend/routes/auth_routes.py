from flask import Blueprint, jsonify, request , g

from backend.auth.jwt_handler import decode_token
from backend.auth.permissions import jwt_required
from backend.services.auth_service import AuthService
from backend.storage.database import get_db_session
from backend.storage.models import User
from sqlalchemy import func, select


auth_bp = Blueprint('auth_bp', __name__)


def _resolve_registration_role(requested_role: str) -> str:
    requested_role = (requested_role or 'staff').strip().lower()
    if requested_role not in ('staff', 'manager', 'admin'):
        requested_role = 'staff'

    with get_db_session() as session:
        user_count = session.execute(select(func.count()).select_from(User)).scalar_one()
        if user_count == 0:
            return 'admin'

    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        try:
            payload = decode_token(auth_header.split(' ', 1)[1])
            if payload.get('role') == 'admin':
                return requested_role
        except Exception:
            pass

    return 'staff'


@auth_bp.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get('username') or '').strip()
    email = str(payload.get('email') or '').strip()
    password = str(payload.get('password') or '')
    requested_role = str(payload.get('role') or 'staff').strip().lower()

    if not username or not email or not password:
        return jsonify({'error': 'Username, email and password are required'}), 400

    role = _resolve_registration_role(requested_role)

    with get_db_session() as session:
        service = AuthService(session)
        try:
            user = service.register_user(username=username, email=email, password=password, role=role)
            result = user.to_dict()
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400

    return jsonify(result)


@auth_bp.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get('username') or '').strip()
    password = str(payload.get('password') or '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    with get_db_session() as session:
        service = AuthService(session)
        user = service.authenticate(username=username, password=password)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        tokens = service.issue_tokens(user)
        response = jsonify({
            'user': user.to_dict(),
            **tokens,
        })

    return response


@auth_bp.route('/api/auth/refresh', methods=['POST'])
def api_auth_refresh():
    payload = request.get_json(silent=True) or {}
    refresh_token = str(payload.get('refresh_token') or '')

    if not refresh_token:
        return jsonify({'error': 'Refresh token is required'}), 400

    with get_db_session() as session:
        service = AuthService(session)
        tokens = service.refresh_tokens(refresh_token)
        if not tokens:
            return jsonify({'error': 'Invalid refresh token'}), 401

    return jsonify(tokens)


@auth_bp.route('/api/auth/logout', methods=['POST'])
@jwt_required
def api_auth_logout():
    current_user = getattr(g, 'current_user', {}) or {}
    user_id = int(current_user.get('sub', 0))

    with get_db_session() as session:
        service = AuthService(session)
        user = service.repository.get_by_id(user_id)
        if user:
            service.revoke_refresh_token(user)

    return jsonify({'ok': True})


@auth_bp.route('/api/auth/status', methods=['GET'])
@jwt_required
def api_auth_status():
    current_user = getattr(g, 'current_user', {}) or {}
    return jsonify({'user': current_user})
