from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings


async def send_email_async(subject: str, body: str, to_email: str):
    message = EmailMessage()
    message["From"] = "alberv0r@yandex.ru"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname="smtp.yandex.ru",
        port=465,
        username=settings.EMAIL.NAME,
        password=settings.EMAIL.PASS,
        use_tls=True,
    )
