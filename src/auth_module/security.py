from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)

def verify_password(hashed: str, password: str) -> str:
    try:
        return _ph.verify(hashed, password)
    except VerifyMismatchError:
        return False