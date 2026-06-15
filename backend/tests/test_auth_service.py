from backend.services.auth_service import AuthService
from backend.auth.jwt_handler import decode_token


def test_register_and_authenticate_user(db_session):
    auth_service = AuthService(db_session)
    user = auth_service.register_user(
        username='testuser',
        email='testuser@example.com',
        password='securepassword',
        role='staff',
    )

    assert user.username == 'testuser'
    assert user.email == 'testuser@example.com'
    assert user.role == 'staff'
    assert user.password_hash != 'securepassword'

    authenticated = auth_service.authenticate('testuser', 'securepassword')
    assert authenticated is not None
    assert authenticated.username == 'testuser'

    tokens = auth_service.issue_tokens(authenticated)
    assert 'access_token' in tokens
    assert 'refresh_token' in tokens
    assert tokens['token_type'] == 'bearer'
    assert isinstance(tokens['expires_in'], int)

    decoded = decode_token(tokens['access_token'])
    assert decoded['sub'] == str(user.id)
    assert decoded['role'] == 'staff'

    refreshed = auth_service.refresh_tokens(tokens['refresh_token'])
    assert refreshed is not None
    assert refreshed['access_token'] != tokens['access_token']


def test_authentication_with_invalid_password(db_session):
    auth_service = AuthService(db_session)
    auth_service.register_user(
        username='anotheruser',
        email='another@example.com',
        password='password1',
        role='staff',
    )

    authenticated = auth_service.authenticate('anotheruser', 'wrongpassword')
    assert authenticated is None
