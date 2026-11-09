from pydantic import EmailStr, BaseModel, field_validator
from auth_module.validators import validate_password


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
    
    
class ResendRequest(BaseModel):
    email: EmailStr