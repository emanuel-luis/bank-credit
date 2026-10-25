import logging
from functools import lru_cache

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

from bank_credit.app.config import get_settings

logger = logging.getLogger("bank_credit.email")


@lru_cache
def get_fastmail() -> FastMail:
    s = get_settings()
    conf = ConnectionConfig(
        MAIL_USERNAME=s.mail_username,
        MAIL_PASSWORD=s.mail_password.get_secret_value(),
        MAIL_FROM=s.mail_from,
        MAIL_PORT=s.mail_port,
        MAIL_SERVER=s.mail_server,
        MAIL_FROM_NAME=s.mail_from_name,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
    )
    return FastMail(conf)


async def send_notification_email(email_to: EmailStr, subject: str, body: str):
    """
    Envia um email de notificação para o usuário (apenas registra no log se MAIL_ENABLED=false)
    """
    if not get_settings().mail_enabled:
        logger.info("Email disabled; would send to %s: %s", email_to, subject)
        return

    message = MessageSchema(subject=subject, recipients=[email_to], body=body, subtype="html")

    await get_fastmail().send_message(message)


async def send_credit_request_status_email(email_to: EmailStr, request_id: int, status: str):
    """
    Envia um email sobre a atualização do status de uma solicitação de crédito
    """
    subject = f"Atualização da Solicitação de Crédito #{request_id}"
    body = f"""
    <html>
        <body>
            <h2>Atualização de Status</h2>
            <p>Sua solicitação de crédito #{request_id} foi atualizada.</p>
            <p>Novo status: <strong>{status}</strong></p>
            <p>Para mais detalhes, acesse sua área do cliente.</p>
        </body>
    </html>
    """

    await send_notification_email(email_to, subject, body)


async def send_welcome_email(email_to: EmailStr, username: str):
    """
    Envia um email de boas-vindas para novos usuários
    """
    subject = "Bem-vindo ao Sistema de Crédito Bancário"
    body = f"""
    <html>
        <body>
            <h2>Bem-vindo, {username}!</h2>
            <p>Sua conta foi criada com sucesso no nosso sistema de crédito bancário.</p>
            <p>Agora você pode:</p>
            <ul>
                <li>Solicitar crédito</li>
                <li>Acompanhar suas solicitações</li>
                <li>Receber notificações importantes</li>
            </ul>
            <p>Qualquer dúvida, estamos à disposição.</p>
        </body>
    </html>
    """

    await send_notification_email(email_to, subject, body)
