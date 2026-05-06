"""Domain-specific errors for the lab skeleton."""


class LabError(Exception):
    """Base error for the lab package."""


class StudentTodoError(LabError):
    """Raised where learners are expected to implement core logic."""


class AgentExecutionError(LabError):
    """Raised when an agent or service execution fails."""


class ValidationError(LabError):
    """Raised when state or output validation fails."""
