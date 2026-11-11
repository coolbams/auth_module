import uuid
import math
import secrets
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from auth_module.models import User
from auth_module.config import settings
from auth_module.database import get_db
from auth_module.dependencies import get_current_user
from auth_module.mailer import send_verification_email
from auth_module.security import hash_password, verify_password
from auth_module.schemas import RegisterRequest, LoginRequest, ResendRequest
from auth_module.tokens import ExpiredToken, InvalidToken, create_verification_token, read_verification_token


log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def send_new_verification(user:User, db: Session) -> None:
    """ Send a fresh link. Every link sent before this one stops working. """
    
    user.verification_nonce = secrets.token_hex(8)
    token = create_verification_token(str(user.id), user.verification_nonce)
    send_verification_email(user.email, token)
    user.last_verification_sent_at = datetime.now(timezone.utc)
    db.commit()
    

@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        log.warning("Duplicate registration for %s", body.email)
        raise HTTPException(409, "Email already registered")
    
    try:
        send_new_verification(user, db)        
    except Exception:
        db.rollback()
        log.exception("Failed to send verification email to %s", user.email)

    log.info("Registered user id=%s", user.id)
    return {"message": "Registered. Check your email to verify your account."}




@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(
        select(User)
        .where(User.email == body.email.lower())).scalar_one_or_none()
    
    if not user or not verify_password(user.password_hash, body.password):
        log.warning("Failed login for %s", body.email)
        raise HTTPException(401, "Invalid email or password")
    
    if not user.is_verified:
        raise HTTPException(403, "Please verify your email first")
    
    log.info("Login ok user id=%s", user.id)
    return {"message" : "Logged in"}




@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    
    try:
        user_id, nonce = read_verification_token(token)
    except ExpiredToken:
        raise HTTPException(400, "Verification link expired. Request a new one.")
    except InvalidToken:
        raise HTTPException(400, "Invalid verification link.")
    
    
    user = db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(400, "Invalid verification link.")
    
    if user.is_verified:                          # clicking twice is still fine
        return {"message": "Email verified. You can log in now."}

    if user.verification_nonce != nonce:
        raise HTTPException(400, "This link is outdated. Use the latest email we sent you.")

    user.is_verified = True
    user.verification_nonce = None               
    db.commit()
    log.info("Email verified user id=%s", user.id)
    return {"message": "Email verified. You can log in now."}




@router.post("/resend-verification")
def resend_verification(body: ResendRequest, db: Session = Depends(get_db)):
    generic = {"message": "If that account exists and isn't verified, a new email has been sent."}
    
    user = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if not user or user.is_verified:
        return generic 

    if user.last_verification_sent_at:
        elapsed = (datetime.now(timezone.utc) - user.last_verification_sent_at).total_seconds()
        wait = math.ceil(settings.resend_cooldown_seconds - elapsed)
        if wait > 0:
            raise HTTPException(
                429,
                f"Please wait {wait} seconds before requesting another email",
                headers={"Retry-After": str(wait)},
            )
            
    try:
        send_new_verification(user, db)
    except Exception:
        log.exception("Failed to resend verification email to %s", user.email)
        raise HTTPException(503, "Could not send the email right now. Try again later.")

    log.info("Verification email resent user id=%s", user.id)
    return generic







@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email}
