
from datetime import datetime, timedelta, timezone

import jwt

from app.auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plain_text():
    password = "StrongPass123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("StrongPass123!")

    assert not verify_password("WrongPassword123!", hashed)


def test_create_and_decode_access_token():
    token = create_access_token(123)

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert "exp" in payload


def test_decode_access_token_rejects_invalid_token():
    try:
        decode_access_token("invalid.token.value")
        assert False, "Expected invalid token to be rejected"
    except jwt.InvalidTokenError:
        pass


def test_decode_access_token_rejects_expired_token():
    expired_payload = {
        "sub": "123",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }

    expired_token = jwt.encode(
        expired_payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    try:
        decode_access_token(expired_token)
        assert False, "Expected expired token to be rejected"
    except jwt.ExpiredSignatureError:
        pass
