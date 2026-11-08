from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from auth_module.config import settings

_serializer = URLSafeTimedSerializer(settings.secret_key, salt="email-verification")


class InvalidToken(Exception):
    """Token is malformed or was tampered with."""


class ExpiredToken(Exception):
    """Token was valid but is older than the allowed lifetime."""


def create_verification_token(user_id: str) -> str:
    return _serializer.dumps(str(user_id))


def read_verification_token(token: str) -> str:
    """Return the user id inside the token, or raise InvalidToken / ExpiredToken."""
    max_age = settings.verification_token_expire_minutes * 60
    try:
        return _serializer.loads(token, max_age=max_age)
    except SignatureExpired:      # must come first: it's a subclass of BadSignature
        raise ExpiredToken
    except BadSignature:
        raise InvalidToken