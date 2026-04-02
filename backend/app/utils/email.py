import smtplib
import os
from email.message import EmailMessage

def send_email(to_email: str, subject: str, message: str) -> None:
    """Send an alert email using Gmail SMTP and environment variables."""
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    
    if not EMAIL_USER or not EMAIL_PASS:
        print(f"Would send email to {to_email} but credentials missing. msg: {message}")
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = list(to_email) if isinstance(to_email, list) else to_email
    msg.set_content(message)

    try:
        # Use SMTP_SSL for standard Gmail port 465
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print(f"Alert email successfully sent.")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")

def send_otp_email(to_email: str, otp: str, is_reset: bool = False) -> None:
    """Send an OTP code for registration or password reset."""
    subject = "ClimaScope Password Reset OTP" if is_reset else "ClimaScope Verification OTP"
    message = f"Your Verification OTP is {otp}.\n\nThis OTP is valid for 15 minutes. Please do not share it with anyone."
    send_email(to_email, subject, message)
