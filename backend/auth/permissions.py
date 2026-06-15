from functools import wraps
from flask import request, jsonify, g
from jwt import InvalidTokenError

from backend.auth.jwt_handler import decode_token


def _get_bearer_token() -> str | None:
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ', 1)[1].strip()
    return request.cookies.get('access_token')


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _get_bearer_token()
        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        try:
            payload = decode_token(token)
            if payload.get('type') != 'access':
                raise InvalidTokenError('Invalid token type')
        except InvalidTokenError as exc:
            return jsonify({'error': 'Invalid or expired token', 'details': str(exc)}), 401

        g.current_user = payload
        return fn(*args, **kwargs)

    return wrapper


def requires_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required
        def wrapper(*args, **kwargs):
            current_user = getattr(g, 'current_user', {}) or {}
            user_role = current_user.get('role')
            if user_role not in roles:
                return jsonify({'error': 'Forbidden', 'details': 'Insufficient permissions'}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
