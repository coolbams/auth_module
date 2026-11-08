import uuid
import logging
from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from auth_module.config import settings
from auth_module.database import get_db
from auth_module.models import UserSessions, User

log = logging.getLogger(__name__)


def get_current_user(
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    db: Session = Depends(get_db)
)-> User:
    
    """
    Return the logged-in user for this request, or raise 401.

    Flow: cookie -> session id -> session row -> user_id -> user

    Used as a FastAPI dependency. Add `user: User = Depends(get_current_user)`
    to any route to protect it; the route body only runs if this returns.

    Raises:
        HTTPException(401): no cookie, malformed id, unknown session,
        or expired session (expired rows are deleted).
    """
    
    if not session_id:
        raise HTTPException(401, "Not logged in")
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(401, "Not logged in")
    
    session = db.get(UserSessions, sid)
    if not session or session.expires_at < datetime.now(timezone.utc):
        if session:
            db.delete(session)
            db.commit()
        raise HTTPException(401, "Session expired")
    
    return db.get(User, session.user_id)