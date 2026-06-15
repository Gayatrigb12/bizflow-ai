import os
import secrets
from datetime import datetime, timedelta
from flask import current_app
import jwt


def _get_config(name: str, default: str) -> str:
    try:
        return current_app.config.get(name, os.getenv(name, default))
    except RuntimeError:
        return os.getenv(name, default)


def get_access_token_expires_seconds() -> int:
    minutes = int(_get_config('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', '15'))
    return minutes * 60


def create_access_token(subject: int, role: str, expires_minutes: int | None = None) -> str:
    expires = datetime.utcnow() + timedelta(minutes=int(expires_minutes or _get_config('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', '15')))
    payload = {
        'sub': str(subject),
        'role': role,
        'type': 'access',
        'exp': expires,
        'iat': datetime.utcnow(),
        'jti': secrets.token_urlsafe(8),
    }
    secret = _get_config('JWT_SECRET_KEY', 'bizflow-ai-secret-key')
    algorithm = _get_config('JWT_ALGORITHM', 'HS256')
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def decode_token(token: str, verify_exp: bool = True) -> dict:
    secret = _get_config('JWT_SECRET_KEY', 'bizflow-ai-secret-key')
    algorithm = _get_config('JWT_ALGORITHM', 'HS256')
    return jwt.decode(token, secret, algorithms=[algorithm], options={'verify_exp': verify_exp})
