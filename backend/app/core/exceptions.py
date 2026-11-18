"""Domain exceptions and HTTP error mapping for Netra."""

from fastapi import HTTPException, status


class NetraException(Exception):
    """Base exception for all Netra platform errors."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ResourceNotFoundException(NetraException):
    """Raised when a requested resource (case, patient, model) does not exist."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(f"{resource_type} '{resource_id}' not found.")
        self.resource_type = resource_type
        self.resource_id = resource_id


class QualityGateRejectionException(NetraException):
    """Raised when an ungradable image fails the quality gate and blocks inference."""
    def __init__(self, reason: str, issues: list[str]):
        super().__init__(f"Image ungradable: {reason}")
        self.reason = reason
        self.issues = issues


class InvalidWorkflowStateException(NetraException):
    """Raised when an operation is invalid for the current case status."""
    def __init__(self, current_status: str, operation: str):
        super().__init__(f"Operation '{operation}' invalid for case in status '{current_status}'.")
        self.current_status = current_status
        self.operation = operation
