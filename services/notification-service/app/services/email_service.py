import smtplib
import ssl

from email.message import EmailMessage
from email.utils import formataddr

import httpx

from app.config import settings


BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def email_is_configured() -> bool:
    provider = settings.email_provider.lower()

    if provider == "brevo":
        return bool(
            settings.brevo_api_key
            and settings.brevo_sender_email
        )

    if provider == "smtp":
        return bool(
            settings.smtp_username
            and settings.smtp_password
            and settings.smtp_from_email
        )

    return False


def send_brevo_email(
    to_email: str,
    subject: str,
    body: str,
):
    if not settings.brevo_api_key:
        raise RuntimeError(
            "Brevo API key is not configured."
        )

    if not settings.brevo_sender_email:
        raise RuntimeError(
            "Brevo sender email is not configured."
        )

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": settings.brevo_api_key,
    }

    payload = {
        "sender": {
            "name": settings.brevo_sender_name,
            "email": settings.brevo_sender_email,
        },
        "to": [
            {
                "email": to_email,
            }
        ],
        "subject": subject,
        "textContent": body,
    }

    with httpx.Client(
        timeout=30.0
    ) as client:

        response = client.post(
            BREVO_URL,
            headers=headers,
            json=payload,
        )

    if response.status_code not in (
        200,
        201,
        202,
    ):
        raise RuntimeError(
            f"Brevo API error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    try:
        data = response.json()
    except Exception:
        data = {}

    return {
        "provider": "brevo",
        "message_id": data.get(
            "messageId"
        ),
    }


def send_smtp_email(
    to_email: str,
    subject: str,
    body: str,
):
    if not settings.smtp_username:
        raise RuntimeError(
            "SMTP username is not configured."
        )

    if not settings.smtp_password:
        raise RuntimeError(
            "SMTP password is not configured."
        )

    if not settings.smtp_from_email:
        raise RuntimeError(
            "SMTP sender email is not configured."
        )

    message = EmailMessage()

    message["Subject"] = subject

    message["From"] = formataddr(
        (
            settings.smtp_from_name,
            settings.smtp_from_email,
        )
    )

    message["To"] = to_email

    message.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=20,
    ) as server:

        server.ehlo()

        if settings.smtp_use_tls:
            server.starttls(
                context=context
            )
            server.ehlo()

        server.login(
            settings.smtp_username,
            settings.smtp_password,
        )

        server.send_message(
            message
        )

    return {
        "provider": "smtp",
        "message_id": None,
    }


def send_email(
    to_email: str,
    subject: str,
    body: str,
):
    provider = (
        settings.email_provider
        .lower()
        .strip()
    )

    if provider == "brevo":
        return send_brevo_email(
            to_email=to_email,
            subject=subject,
            body=body,
        )

    if provider == "smtp":
        return send_smtp_email(
            to_email=to_email,
            subject=subject,
            body=body,
        )

    raise RuntimeError(
        f"Unsupported email provider: "
        f"{provider}"
    )
