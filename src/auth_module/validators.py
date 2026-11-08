import re

MIN_LEN = 8
MAX_LEN = 128

def validate_password(password: str) -> list[str]:
    """Return a list of problems. Empty list means the password is fine."""

    problems = []
    if len(password) < MIN_LEN:
        problems.append(f"at least {MIN_LEN} characters")
    if len(password) > MAX_LEN:
        problems.append(f"at most {MAX_LEN} characters")
    if not re.search(r"\d", password):
        problems.append("at least one digit")
    if not re.search(r"[^A-Za-z0-9]", password):   # anything that isn't a letter or digit
        problems.append("at least one special character")
    return problems

