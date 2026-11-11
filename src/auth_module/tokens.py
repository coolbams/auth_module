from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from auth_module.config import settings

_serializer = URLSafeTimedSerializer(settings.secret_key, salt="email-verification")


class InvalidToken(Exception):
    """Token is malformed or was tampered with."""


class ExpiredToken(Exception):
    """Token was valid but is older than the allowed lifetime."""


def create_verification_token(user_id: str, nonce: str) -> str:
    return _serializer.dumps({"uid":str(user_id), "n":nonce})



def read_verification_token(token:str) -> tuple[str, str]:
    """Return (user_id, nonce), or raise InvalidToken / ExpiredToken. """
    
    max_age = settings.verification_token_expire_minutes * 60
    try:
        data = _serializer.loads(token, max_age=max_age)
        return data["uid"], data["n"]
    except SignatureExpired:
        raise ExpiredToken
    except (BadSignature, KeyError, TypeError):
        raise InvalidToken