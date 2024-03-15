from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings


async def send_email_async(subject: str, body: str, to_email: str):
    """
    Асинхронная отправка электронного письма.

    Функция асинхронно отправляет электронное письмо с использованием SMTP сервера.
    Поддерживает TLS для безопасной передачи данных. Для отправки используются настройки,
    указанные в конфигурации приложения (settings).

    Args:
        subject (str): Тема электронного письма.
        body (str): Текстовое содержание письма.
        to_email (str): Адрес электронной почты получателя.

    Пример использования:
        await send_email_async(
            subject="Привет от FastAPI",
            body="Тестовое сообщение от вашего FastAPI приложения.",
            to_email="recipient@example.com"
        )

    Важно: Для функционирования необходимо иметь доступ к SMTP-серверу и корректно настроенные
    параметры в settings.EMAIL, включая имя пользователя и пароль.
    """

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
