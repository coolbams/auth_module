from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    secret_key: str
    session_cookie_name: str = "session_id"
    session_lifetime_days: int = 7
    cookie_secure: bool = False        # set True when you're on HTTPS
    verification_token_expire_minutes: int = 15
    resend_cooldown_seconds: int = 20
    
    # Mail Setup
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    email_from: str = "no-reply@example.com"
    base_url: str = "http://localhost:8000"   # where the verify link points
    
settings = Settings()