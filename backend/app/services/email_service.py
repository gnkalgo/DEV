import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings


class EmailService:
    def enabled(self) -> bool:
        return bool(settings.smtp_host and settings.smtp_from)

    async def send(self, to_email: str, subject: str, text: str, html: str | None = None) -> None:
        if not self.enabled():
            raise RuntimeError("SMTP is not configured")
        await asyncio.to_thread(self._send_sync, to_email, subject, text, html)

    def _send_sync(self, to_email: str, subject: str, text: str, html: str | None) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{settings.app_name} <{settings.smtp_from}>"
        msg["To"] = to_email
        msg.set_content(text)
        if html:
            msg.add_alternative(html, subtype="html")

        context = ssl.create_default_context()
        use_ssl = settings.smtp_ssl or settings.smtp_port == 465

        if use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20, context=context) as smtp:
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
            return

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.ehlo()
            if settings.smtp_starttls:
                smtp.starttls(context=context)
                smtp.ehlo()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)

    async def send_verification(self, to_email: str, verify_url: str) -> None:
        text = (
            f"Welcome to {settings.app_name}.\n\n"
            f"Verify your email by opening this link (valid 24 hours):\n{verify_url}\n\n"
            "If you did not create this account, ignore this email."
        )
        html = f"""
        <p>Welcome to <strong>{settings.app_name}</strong>.</p>
        <p>Verify your email (valid 24 hours):</p>
        <p><a href="{verify_url}">{verify_url}</a></p>
        <p>If you did not create this account, ignore this email.</p>
        """
        await self.send(to_email, f"Verify your {settings.app_name} email", text, html)

    async def send_password_reset(self, to_email: str, reset_url: str) -> None:
        text = (
            f"Reset your {settings.app_name} password using this link (valid 1 hour):\n{reset_url}\n\n"
            "If you did not request this, ignore this email."
        )
        html = f"""
        <p>Reset your <strong>{settings.app_name}</strong> password (valid 1 hour):</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>If you did not request this, ignore this email.</p>
        """
        await self.send(to_email, f"Reset your {settings.app_name} password", text, html)

    async def send_renewal_reminder(
        self,
        to_email: str,
        pay_url: str,
        plan_label: str,
        amount_inr: int,
        expires_at,
    ) -> None:
        expires_str = expires_at.strftime("%Y-%m-%d %H:%M UTC") if expires_at else "soon"
        text = (
            f"Your {settings.app_name} plan ({plan_label}) expires on {expires_str}.\n\n"
            f"Auto-renew is on. Pay ₹{amount_inr} via UPI to extend without losing access:\n{pay_url}\n\n"
            "After paying, open the link and submit your UTR. We confirm within a few hours."
        )
        html = f"""
        <p>Your <strong>{settings.app_name}</strong> plan <strong>{plan_label}</strong> expires on {expires_str}.</p>
        <p>Auto-renew is enabled. Pay <strong>₹{amount_inr}</strong> via UPI:</p>
        <p><a href="{pay_url}">{pay_url}</a></p>
        <p>Submit your UTR on that page after payment.</p>
        """
        await self.send(to_email, f"{settings.app_name} subscription renewal", text, html)


email_service = EmailService()
