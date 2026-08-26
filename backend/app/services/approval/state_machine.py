from enum import Enum
from typing import Dict, List, Optional
from app.core.errors import BadRequestError
from app.models.application import Application


class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    STAGED_FOR_PREPARATION = "staged_for_preparation"
    ACTION_REQUIRED = "action_required"
    REQUIRES_REAPPROVAL = "requires_reapproval"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    ARCHIVED = "archived"


ALLOWED_TRANSITIONS: Dict[ApplicationStatus, List[ApplicationStatus]] = {
    ApplicationStatus.DRAFT: [
        ApplicationStatus.READY_FOR_REVIEW,
        ApplicationStatus.ARCHIVED,
    ],
    ApplicationStatus.READY_FOR_REVIEW: [
        ApplicationStatus.IN_REVIEW,
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ARCHIVED,
    ],
    ApplicationStatus.IN_REVIEW: [
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.READY_FOR_REVIEW,
        ApplicationStatus.ARCHIVED,
    ],
    ApplicationStatus.APPROVED: [
        ApplicationStatus.STAGED_FOR_PREPARATION,
        ApplicationStatus.ACTION_REQUIRED,
        ApplicationStatus.REQUIRES_REAPPROVAL,
        ApplicationStatus.REJECTED,
        ApplicationStatus.IN_REVIEW,
        ApplicationStatus.ARCHIVED,
    ],
    ApplicationStatus.STAGED_FOR_PREPARATION: [
        ApplicationStatus.APPROVED,
        ApplicationStatus.ACTION_REQUIRED,
        ApplicationStatus.REQUIRES_REAPPROVAL,
        ApplicationStatus.IN_REVIEW,
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.ARCHIVED,
    ],
    ApplicationStatus.ACTION_REQUIRED: [
        ApplicationStatus.STAGED_FOR_PREPARATION,
        ApplicationStatus.APPROVED,
        ApplicationStatus.REQUIRES_REAPPROVAL,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ARCHIVED,
    ],
    ApplicationStatus.REQUIRES_REAPPROVAL: [
        ApplicationStatus.IN_REVIEW,
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ARCHIVED,
    ],
    ApplicationStatus.REJECTED: [
        ApplicationStatus.READY_FOR_REVIEW,
        ApplicationStatus.IN_REVIEW,
        ApplicationStatus.ARCHIVED,
    ],
    ApplicationStatus.SUBMITTED: [
        ApplicationStatus.ARCHIVED,
    ],
    ApplicationStatus.ARCHIVED: [
        ApplicationStatus.READY_FOR_REVIEW,
        ApplicationStatus.DRAFT,
    ],
}


def validate_transition(current_status: str, target_status: str) -> None:
    """Validate that state transition follows strict application state machine."""
    try:
        current_enum = ApplicationStatus(current_status)
    except ValueError:
        raise BadRequestError(f"Current application status '{current_status}' is invalid.")

    try:
        target_enum = ApplicationStatus(target_status)
    except ValueError:
        raise BadRequestError(f"Target application status '{target_status}' is invalid.")

    allowed = ALLOWED_TRANSITIONS.get(current_enum, [])
    if target_enum not in allowed and current_enum != target_enum:
        allowed_names = [s.value for s in allowed]
        raise BadRequestError(
            f"Illegal application state transition from '{current_status}' to '{target_status}'. "
            f"Allowed next states: {allowed_names}"
        )


def transition_application(
    application: Application,
    target_status: str,
    reason: Optional[str] = None,
) -> Application:
    """Apply strict state machine transition to an application entity."""
    validate_transition(application.status, target_status)
    application.status = target_status
    if reason:
        application.invalidation_reason = reason
    return application
