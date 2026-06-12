import bcrypt
from typing import Optional

from backend.auth.jwt_handler import create_access_token, create_refresh_token, get_access_token_expires_seconds
from backend.storage.repositories.user_repository import UserRepository
from backend.storage.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


class AuthService:
    def __init__(self, session):
        self.repository = UserRepository(session)

    def register_user(self, username: str, email: str, password: str, role: str = 'staff') -> User:
        if not username.strip() or not email.strip() or not password:
            raise ValueError('Username, email and password are required')

        normalized_username = username.strip()
        normalized_email = email.strip().lower()
        existing = self.repository.get_by_username(normalized_username)
        if existing:
            raise ValueError('Username already exists')

        if role not in ('staff', 'manager', 'admin'):
            role = 'staff'

        user = User(
            username=normalized_username,
            email=normalized_email,
            password_hash=hash_password(password),
            role=role,
        )
        return self.repository.create(user)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.repository.get_by_username(username.strip())
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    def issue_tokens(self, user: User) -> dict:
        access_token = create_access_token(subject=user.id, role=user.role)
        refresh_token = create_refresh_token()
        user.refresh_token_hash = hash_password(refresh_token)
        self.repository.create(user)
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': get_access_token_expires_seconds(),
        }

    def refresh_tokens(self, refresh_token: str) -> Optional[dict]:
        user = self.repository.get_by_refresh_token(refresh_token)
        if not user:
            return None

        return self.issue_tokens(user)

    def revoke_refresh_token(self, user: User) -> None:
        user.refresh_token_hash = None
        self.repository.create(user)
