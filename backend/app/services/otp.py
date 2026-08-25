import asyncio
from datetime import datetime, timedelta, timezone
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import logging
import secrets
import smtplib
from typing import Dict, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger("app.services.otp")


class OTPRecord:
    def __init__(self, code: str, purpose: str, expires_at: datetime):
        self.code = code
        self.purpose = purpose
        self.expires_at = expires_at
        self.attempts = 0
        self.last_sent_at = datetime.now(timezone.utc)
        self.verified = False


class OTPService:
    """
    Cryptographically secure One-Time Password (OTP) service with Gmail SMTP email delivery,
    rate-limiting, automatic expiry, and brute-force attempt protection.
    """

    def __init__(self):
        # In-memory storage: key is f"{email.lower()}:{purpose.lower()}"
        self._store: Dict[str, OTPRecord] = {}

    def _get_key(self, email: str, purpose: str = "registration") -> str:
        return f"{email.strip().lower()}:{purpose.strip().lower()}"

    def generate_otp(self, email: str, purpose: str = "registration") -> Tuple[str, bool, Optional[str]]:
        """
        Generates a 6-digit OTP for the given email and purpose.
        Enforces a 60-second cooldown between resends.
        Returns: (otp_code, is_new, error_message)
        """
        now = datetime.now(timezone.utc)
        key = self._get_key(email, purpose)

        existing = self._store.get(key)
        if existing and now < existing.expires_at:
            time_since_last = (now - existing.last_sent_at).total_seconds()
            if time_since_last < settings.OTP_RESEND_COOLDOWN_SECONDS:
                remaining = int(settings.OTP_RESEND_COOLDOWN_SECONDS - time_since_last)
                return (
                    "",
                    False,
                    f"Please wait {remaining} seconds before requesting a new verification code.",
                )

        # Generate cryptographically secure 6-digit numeric code
        code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        record = OTPRecord(code=code, purpose=purpose, expires_at=expires_at)
        self._store[key] = record

        # Cleanup expired records periodically
        self._cleanup_expired()

        return code, True, None

    def verify_otp(self, email: str, code: str, purpose: str = "registration") -> Tuple[bool, str]:
        """
        Verifies the OTP code for an email and purpose.
        Returns (success: bool, message: str).
        """
        now = datetime.now(timezone.utc)
        key = self._get_key(email, purpose)
        record = self._store.get(key)

        # Allow fallback testing code in development
        if code in ("999999", "123456") and settings.ENVIRONMENT == "development":
            if record:
                record.verified = True
            return True, "Code verified successfully."

        if not record:
            return False, "No active verification code found for this email. Please request a new code."

        if now > record.expires_at:
            del self._store[key]
            return False, "The verification code has expired. Please request a new one."

        record.attempts += 1
        if record.attempts > 5:
            del self._store[key]
            return False, "Too many invalid attempts. This verification code has been invalidated. Please request a new one."

        if record.code != code.strip():
            remaining = 5 - record.attempts
            return False, f"Incorrect verification code. {remaining} attempt(s) remaining."

        record.verified = True
        # Mark as consumed by deleting from store
        del self._store[key]
        return True, "Code verified successfully."

    def is_already_verified(self, email: str, purpose: str = "registration") -> bool:
        """Checks if the email had an OTP recently verified."""
        key = self._get_key(email, purpose)
        record = self._store.get(key)
        return bool(record and record.verified)

    def _cleanup_expired(self):
        """Removes expired records to prevent unbounded memory growth."""
        now = datetime.now(timezone.utc)
        keys_to_delete = [k for k, v in self._store.items() if now > v.expires_at]
        for k in keys_to_delete:
            self._store.pop(k, None)

    def _send_smtp_sync(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Synchronous SMTP email sender designed to run inside asyncio.to_thread."""
        sender_email = settings.SMTP_USER or settings.EMAILS_FROM_EMAIL
        sender_password = settings.SMTP_PASSWORD
        sender_name = settings.EMAILS_FROM_NAME

        if not sender_email or not sender_password:
            logger.warning("SMTP credentials not configured. Skipping live email dispatch.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((str(Header(sender_name, "utf-8")), sender_email))
        msg["To"] = to_email

        # Attach text & html alternatives
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            if settings.SMTP_SSL or settings.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
                if settings.SMTP_TLS:
                    server.starttls()

            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [to_email], msg.as_string())
            server.quit()
            logger.info(f"Successfully sent OTP email to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via SMTP to {to_email}: {e}", exc_info=True)
            return False

    async def send_otp_email(self, email: str, purpose: str = "registration") -> Tuple[bool, str]:
        """
        Generates and dispatches a verification email containing a 6-digit OTP.
        Returns: (success: bool, message: str)
        """
        otp_code, is_new, err = self.generate_otp(email, purpose)
        if not is_new:
            return False, err or "Rate limit reached. Please wait before requesting another code."

        # Purpose title mapping
        purpose_titles = {
            "registration": "Verify Your Email for Client Magnet",
            "login": "Your Client Magnet Login Code",
            "password_reset": "Reset Your Client Magnet Password",
            "verification": "Client Magnet Verification Code",
        }
        subject = purpose_titles.get(purpose.lower(), "Your Client Magnet Verification Code")

        text_content = (
            f"Hello,\n\n"
            f"Your verification code for Client Magnet is: {otp_code}\n\n"
            f"This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
            f"If you did not request this code, please ignore this email.\n\n"
            f"— The Client Magnet Team"
        )

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #020617; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #020617; padding: 40px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 520px; background-color: #0f172a; border-radius: 16px; border: 1px solid #1e293b; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);">
          <!-- Header -->
          <tr>
            <td style="padding: 32px 32px 20px 32px; text-align: center; border-bottom: 1px solid #1e293b;">
              <div style="display: inline-block; padding: 12px; background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(99, 102, 241, 0.2)); border-radius: 12px; margin-bottom: 12px;">
                <span style="font-size: 24px; font-weight: 800; color: #38bdf8; letter-spacing: -0.5px;">🧲 Client Magnet</span>
              </div>
              <h1 style="margin: 0; font-size: 20px; font-weight: 700; color: #ffffff;">{subject}</h1>
            </td>
          </tr>
          <!-- Body Content -->
          <tr>
            <td style="padding: 32px;">
              <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 24px; color: #94a3b8;">
                Use the one-time verification code below to complete your authentication request:
              </p>
              
              <!-- OTP Box -->
              <div style="background: linear-gradient(135deg, #1e293b, #0f172a); border: 2px dashed #38bdf8; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
                <span style="display: block; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; color: #38bdf8; margin-bottom: 8px;">Your 6-Digit Code</span>
                <span style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #ffffff; text-shadow: 0 0 12px rgba(56, 189, 248, 0.6);">{otp_code}</span>
              </div>

              <p style="margin: 0 0 8px 0; font-size: 13px; line-height: 20px; color: #64748b; text-align: center;">
                ⏳ This code is valid for <strong>{settings.OTP_EXPIRE_MINUTES} minutes</strong> and can only be used once.
              </p>
              <p style="margin: 0; font-size: 13px; line-height: 20px; color: #64748b; text-align: center;">
                If you did not request this verification code, please disregard this email.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color: #020617; padding: 20px 32px; text-align: center; border-top: 1px solid #1e293b;">
              <p style="margin: 0; font-size: 12px; color: #475569;">
                &copy; {datetime.now(timezone.utc).year} Client Magnet &bull; Automated Client Acquisition Platform
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        # Dispatch asynchronously via thread pool
        sent = await asyncio.to_thread(self._send_smtp_sync, email, subject, html_content, text_content)

        if sent:
            return True, f"Verification code sent to {email}. Please check your inbox."
        else:
            # If SMTP failed in development, return success with debug notice
            if settings.ENVIRONMENT == "development":
                logger.info(f"[DEV DEBUG] Generated OTP for {email} ({purpose}): {otp_code}")
                return True, f"Verification code generated (Code: {otp_code} for testing)."
            return False, "Failed to deliver verification email. Please verify your email address and try again."


otp_service = OTPService()
