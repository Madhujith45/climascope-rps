"""
ClimaScope – Email Utilities
Sends OTP and notification emails via SMTP.

Configure via environment variables:
    SMTP_HOST      – SMTP server hostname (default: smtp.gmail.com)
    SMTP_PORT      – SMTP port (default: 587)
    SMTP_USER      – SMTP username / email
    SMTP_PASSWORD  – SMTP password or app-specific password
    SMTP_FROM      – From address (defaults to SMTP_USER)
"""

import logging
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# SMTP Configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USER


def send_otp_email(to_email: str, otp: str) -> bool:
    """Send a password reset OTP email.

    Returns True if the email was sent successfully, False otherwise.
    If SMTP is not configured, logs the OTP to console (dev mode).
    """
    subject = "ClimaScope – Password Reset OTP"
    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px;">
        <div style="max-width: 500px; margin: auto; background: #1e293b; border-radius: 12px; padding: 32px; border: 1px solid #334155;">
            <h2 style="color: #60a5fa; margin-top: 0;">🔐 Password Reset</h2>
            <p>You requested a password reset for your ClimaScope account.</p>
            <p>Your one-time verification code is:</p>
            <div style="text-align: center; margin: 24px 0;">
                <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #60a5fa; 
                             background: #0f172a; padding: 16px 32px; border-radius: 8px; display: inline-block;">
                    {otp}
                </span>
            </div>
            <p style="color: #94a3b8; font-size: 14px;">
                This code expires in <strong>10 minutes</strong>.<br>
                If you didn't request this, please ignore this email.
            </p>
            <hr style="border: 1px solid #334155; margin: 24px 0;">
            <p style="color: #64748b; font-size: 12px; text-align: center;">
                ClimaScope – AI Microclimate Intelligence Platform
            </p>
        </div>
    </body>
    </html>
    """

    # Dev mode: if SMTP not configured, print OTP to console
    if not SMTP_USER or not SMTP_PASSWORD:
        print("\n" + "=" * 60)
        print(f"  🔑 DEV MODE – OTP NOT EMAILED (SMTP not configured)")
        print(f"  ✉️  Email : {to_email}")
        print(f"  🔢  OTP   : {otp}")
        print(f"  ⏱️  Expires in 10 minutes")
        print("  ℹ️  Set SMTP_USER + SMTP_PASSWORD in .env to enable email")
        print("=" * 60 + "\n")
        logger.warning(
            "SMTP not configured – OTP for %s: [see console above]  "
            "(set SMTP_USER and SMTP_PASSWORD in .env)",
            to_email,
        )
        return True  # Pretend success in dev mode

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()  # re-identify after TLS handshake (required by some servers)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())

        logger.info("OTP email sent to %s", to_email)
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed – check SMTP_USER and SMTP_PASSWORD")
        return False
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending email to %s: %s", to_email, exc)
        return False
    except Exception as exc:
        logger.error("Unexpected email error: %s", exc)
        return False


def send_alert_email(to_email: str, message: str, subject: str = "ClimaScope Alert") -> bool:
    """Send an alert email; in dev mode logs to console when SMTP is not configured."""
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #0b1220; color: #e5e7eb; padding: 24px;">
        <div style="max-width: 560px; margin: auto; background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 20px;">
            <h2 style="margin-top: 0; color: #f87171;">ClimaScope Alert</h2>
            <p style="line-height: 1.6;">{message}</p>
            <p style="color: #9ca3af; font-size: 12px;">Generated at {datetime.utcnow().isoformat()} UTC</p>
        </div>
    </body>
    </html>
    """

    if not SMTP_USER or not SMTP_PASSWORD:
        print("\n" + "=" * 60)
        print("  DEV MODE - ALERT EMAIL NOT SENT (SMTP not configured)")
        print(f"  To      : {to_email}")
        print(f"  Subject : {subject}")
        print(f"  Message : {message}")
        print("=" * 60 + "\n")
        logger.warning("SMTP not configured - alert email for %s logged to console", to_email)
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())

        logger.info("Alert email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send alert email to %s: %s", to_email, exc)
        return False
