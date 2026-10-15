"""
NexCart — Notification Service (Push + Email)
================================================
Sends nudge notifications via Firebase Cloud Messaging (push)
and aiosmtplib (email). Gracefully degrades if keys are missing.
"""

import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

import httpx

from backend.utils.logger import get_logger

logger = get_logger("notification")


def _build_html_email(subject: str, body: str, cta_text: str) -> str:
    """Build a branded HTML email template."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background-color:#0A0A0F;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#0A0A0F;">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table role="presentation" width="600" cellspacing="0" cellpadding="0"
               style="background-color:#12121A;border-radius:16px;border:1px solid #1E1E2E;">
          <!-- Header -->
          <tr>
            <td style="background-color:#7C6DDD;padding:24px 32px;border-radius:16px 16px 0 0;">
              <h1 style="margin:0;color:#FFFFFF;font-size:24px;font-weight:700;">
                NexCart
              </h1>
              <p style="margin:4px 0 0;color:#E8E8F0;font-size:13px;opacity:0.85;">
                Supply-Chain Intelligence Platform
              </p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              <h2 style="margin:0 0 16px;color:#E8E8F0;font-size:20px;">
                {subject}
              </h2>
              <p style="margin:0 0 24px;color:#6E6E8A;font-size:15px;line-height:1.6;">
                {body}
              </p>
              <!-- CTA Button -->
              <table role="presentation" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="border-radius:8px;background-color:#1D9E75;">
                    <a href="#" style="display:inline-block;padding:14px 28px;
                       color:#FFFFFF;text-decoration:none;font-size:15px;
                       font-weight:600;border-radius:8px;">
                      {cta_text}
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:20px 32px;border-top:1px solid #1E1E2E;">
              <p style="margin:0;color:#6E6E8A;font-size:12px;line-height:1.5;">
                You are receiving this email because you are a NexCart customer.
                <br>
                <a href="#" style="color:#7C6DDD;text-decoration:underline;">
                  Unsubscribe
                </a>
                &nbsp;|&nbsp;
                <a href="#" style="color:#7C6DDD;text-decoration:underline;">
                  Manage preferences
                </a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


class NotificationService:
    """Sends push and email notifications for nudge campaigns."""

    def __init__(self) -> None:
        self.firebase_key: str = os.getenv("FIREBASE_SERVER_KEY", "")
        self.smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user: str = os.getenv("SMTP_USER", "")
        self.smtp_password: str = os.getenv("SMTP_PASSWORD", "")

    async def send_push(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Send a push notification via Firebase Cloud Messaging.

        Args:
            push_token: FCM device registration token
            title: Notification title
            body: Notification body text
            data: Optional data payload

        Returns:
            bool: True if sent successfully (or gracefully logged)
        """
        if not self.firebase_key:
            logger.warning(
                f"FIREBASE_SERVER_KEY not set — logging push notification: "
                f"token={push_token[:20]}..., title='{title}', body='{body}'"
            )
            return True  # Graceful degradation

        try:
            payload = {
                "to": push_token,
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": "nexcart_icon",
                    "click_action": "OPEN_NUDGE",
                },
                "data": data or {},
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://fcm.googleapis.com/fcm/send",
                    json=payload,
                    headers={
                        "Authorization": f"key={self.firebase_key}",
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", 0) > 0:
                        logger.info(f"Push sent to {push_token[:20]}...")
                        return True
                    else:
                        logger.error(f"FCM push failed: {result}")
                        return False
                else:
                    logger.error(
                        f"FCM HTTP error: {response.status_code} — "
                        f"{response.text}"
                    )
                    return False

        except httpx.HTTPError as exc:
            logger.error(f"FCM HTTP error: {exc}")
            return False
        except Exception as exc:
            logger.error(f"FCM unexpected error: {exc}")
            return False

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        cta_text: str = "View Details",
    ) -> bool:
        """
        Send a branded HTML email via aiosmtplib.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body text
            cta_text: Call-to-action button text

        Returns:
            bool: True if sent successfully (or gracefully logged)
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning(
                f"SMTP credentials not set — logging email: "
                f"to={to_email}, subject='{subject}', body='{body}'"
            )
            return True  # Graceful degradation

        try:
            import aiosmtplib

            html_content = _build_html_email(subject, body, cta_text)

            message = MIMEMultipart("alternative")
            message["From"] = f"NexCart <{self.smtp_user}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Plain text fallback
            message.attach(MIMEText(body, "plain"))
            # HTML version
            message.attach(MIMEText(html_content, "html"))

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=False,
                start_tls=True,
            )

            logger.info(f"Email sent to {to_email}: '{subject}'")
            return True

        except ImportError:
            logger.error("aiosmtplib not installed — cannot send email")
            return False
        except Exception as exc:
            logger.error(f"Email send error: {exc}")
            return False


print("✓ notification.py complete")
