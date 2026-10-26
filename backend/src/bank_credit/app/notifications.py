"""Customer notifications for request outcomes. Customer-facing text is pt-BR."""

from datetime import datetime

from sqlalchemy.orm import Session

from bank_credit.app.domain.enums import RequestStatus
from bank_credit.app.models import CreditRequest, Notification, RequestEvent

_SUBJECTS = {
    RequestStatus.APPROVED: "Solicitação de crédito aprovada",
    RequestStatus.RETURNED: "Solicitação de crédito devolvida",
    RequestStatus.REJECTED: "Solicitação de crédito rejeitada",
    RequestStatus.EXPIRED: "Solicitação de crédito expirada",
}


def notify(
    db: Session, client_id: int, request_id: int | None, subject: str, message: str, now: datetime
) -> Notification:
    notification = Notification(
        client_id=client_id,
        request_id=request_id,
        subject=subject,
        message=message,
        created_at=now,
    )
    db.add(notification)
    return notification


def notify_request_event(
    db: Session, request: CreditRequest, event: RequestEvent
) -> Notification | None:
    """Notify the customer when an event leaves the request approved, returned, rejected or expired."""
    subject = _SUBJECTS.get(event.to_status)
    if subject is None:
        return None
    message = f"Sua solicitação #{request.id} foi atualizada: {subject.lower()}."
    if event.reason:
        message += f" Motivo: {event.reason}"
    return notify(db, request.client_id, request.id, subject, message, event.occurred_at)
