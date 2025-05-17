from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração condicional para ambiente de teste
is_testing = os.getenv("TESTING", "false").lower() == "true"

if is_testing:
    # Configuração mock para testes
    conf = ConnectionConfig(
        MAIL_USERNAME="test@example.com",
        MAIL_PASSWORD="test_password",
        MAIL_FROM="test@example.com",
        MAIL_PORT=587,
        MAIL_SERVER="test_server",
        MAIL_FROM_NAME="Test System",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
    )
else:
    # Configuração real para produção
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
        MAIL_FROM=os.getenv("MAIL_FROM", ""),
        MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
        MAIL_SERVER=os.getenv("MAIL_SERVER", ""),
        MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Sistema de Crédito Bancário"),
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
    )

fastmail = FastMail(conf)


async def send_notification_email(email_to: EmailStr, subject: str, body: str):
    """
    Envia um email de notificação para o usuário
    """
    if is_testing:
        # Em ambiente de teste, apenas simula o envio
        print(f"[TEST] Email would be sent to {email_to}: {subject}")
        return

    message = MessageSchema(subject=subject, recipients=[email_to], body=body, subtype="html")

    await fastmail.send_message(message)


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
