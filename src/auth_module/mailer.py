import logging
import smtplib
from email.message import EmailMessage

from auth_module.config import settings

log = logging.getLogger(__name__)


def send_verification_email(to_email: str, token: str) -> None:
    link = f"{settings.base_url}/auth/verify-email?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "Verify your email"
    msg["From"] = settings.email_from
    msg["To"] = to_email
    msg.set_content(
        "Welcome!\n\n"
        f"Click to verify your email:\n{link}\n\n"
        f"This link expires in {settings.verification_token_expire_minutes} minutes."
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.send_message(msg)

    log.info("Verification email sent to %s", to_email)   # never log the link or token