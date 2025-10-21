from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from typing import List
from loguru import logger
from ..config import settings
from .base_notifier import BaseNotifier
from email.mime.multipart import MIMEMultipart  

class EmailNotifier(BaseNotifier):
    def send(self, subject: str, body: str, recipients: List[str], content_type: str = "plain") -> None:
        if not settings.email_enabled or not recipients:
            return
        if content_type == "html":
            msg = MIMEMultipart("alternative")
            part = MIMEText(body, "html")
            msg.attach(part)
        else:
            msg = MIMEText(body, "plain")

        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = ", ".join(recipients)

        with smtplib.SMTP(settings.email_host, settings.email_port) as server:
            server.starttls()
            server.login(settings.email_user, settings.email_pass)
            server.sendmail(settings.email_from, recipients, msg.as_string())
        logger.info(f"Email sent to {recipients}: {subject}")
