import bcrypt
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.storage.models import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.execute(
            select(User).where(User.username == username.strip())
        ).scalars().first()

    def get_by_refresh_token(self, refresh_token: str) -> Optional[User]:
        users = self.session.execute(select(User)).scalars().all()
        for user in users:
            if not user.refresh_token_hash:
                continue
            try:
                if bcrypt.checkpw(refresh_token.encode('utf-8'), user.refresh_token_hash.encode('utf-8')):
                    return user
            except ValueError:
                continue
        return None

    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user
