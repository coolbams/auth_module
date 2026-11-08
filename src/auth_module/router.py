import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr, BaseModel, field_validator

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


from auth_module.models import User
from auth_module.database import get_db
from auth_module.validators import validate_password
from auth_module.dependencies import get_current_user
from auth_module.mailer import send_verification_email
from auth_module.security import hash_password, verify_password
from auth_module.tokens import ExpiredToken, InvalidToken, create_verification_token, read_verification_token


log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])




class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator("password")
    @classmethod
    def password_rules(cls, value: str) -> str:
        problems = validate_password(value)
        if problems:
            raise ValueError("Password needs " + ", ".join(problems))
        return value
    
    

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
        send_verification_email(user.email, create_verification_token(str(user.id)))
        user.last_verification_sent_at = datetime.now(timezone.utc)
        db.commit()
        
    except Exception:
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
        user_id = read_verification_token(token)
    except ExpiredToken:
        raise HTTPException(400, "Verification link expired. Request a new one.")
    except InvalidToken:
        raise HTTPException(400, "Invalid verification link.")
    
    
    user = db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(400, "Invalid verification link.")
    
    if not user.is_verified:
        user.is_verified = True
        db.commit()
        log.info("Email verified user id=%s", user.id)
    return {"message": "Email verified. You can log in now."}



@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email}
