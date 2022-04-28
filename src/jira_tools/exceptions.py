"""Custom exceptions for JIRA Tools."""


class JiraToolsError(Exception):
    """Base exception for all JIRA Tools errors."""

    pass


class ConfigurationError(JiraToolsError):
    """Raised when there's a configuration issue."""

    pass


class AuthenticationError(JiraToolsError):
    """Raised when authentication fails."""

    pass


class ConnectionError(JiraToolsError):
    """Raised when connection to JIRA server fails."""

    pass


class FetchError(JiraToolsError):
    """Raised when fetching data from JIRA fails."""

    pass
