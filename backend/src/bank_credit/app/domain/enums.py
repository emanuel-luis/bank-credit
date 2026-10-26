"""Enumerations shared by models, the workflow and the API. Values are what the database stores."""

from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    STAFF = "staff"
    MANAGER = "manager"
    ADMIN = "admin"


class RequestStatus(StrEnum):
    IN_REVIEW = "IN_REVIEW"
    RETURNED = "RETURNED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


TERMINAL_STATUSES = frozenset(
    {
        RequestStatus.APPROVED,
        RequestStatus.REJECTED,
        RequestStatus.CANCELLED,
        RequestStatus.EXPIRED,
    }
)


class Action(StrEnum):
    """Actions a user can request through the API."""

    SUBMIT = "submit"
    APPROVE = "approve"
    RETURN = "return"
    RESUBMIT = "resubmit"
    REJECT = "reject"
    CANCEL = "cancel"


class EventType(StrEnum):
    SUBMITTED = "SUBMITTED"
    STAGE_APPROVED = "STAGE_APPROVED"
    RETURNED = "RETURNED"
    RESUBMITTED = "RESUBMITTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    SLA_BREACHED = "SLA_BREACHED"


class JobStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
