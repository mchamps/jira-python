"""JIRA client wrapper with secure authentication and connection handling."""

import logging
from typing import Optional

from jira import JIRA
from jira.exceptions import JIRAError

from jira_tools.config import Config
from jira_tools.exceptions import AuthenticationError, ConnectionError

logger = logging.getLogger(__name__)


class JiraClient:
    """A wrapper around the JIRA client with secure authentication.

    This class provides a clean interface for connecting to JIRA servers
    with proper error handling and logging.

    Attributes:
        config: Configuration object containing connection settings
        client: The underlying JIRA client instance

    Example:
        >>> config = Config.from_env()
        >>> client = JiraClient(config)
        >>> client.connect()
        >>> issues = client.search_issues("project = MYPROJECT")
    """

    def __init__(self, config: Config) -> None:
        """Initialize the JIRA client.

        Args:
            config: Configuration object with connection settings
        """
        self.config = config
        self._client: Optional[JIRA] = None
        logger.info(f"JiraClient initialized for server: {config.server_url}")

    @property
    def client(self) -> JIRA:
        """Get the JIRA client instance, connecting if necessary.

        Returns:
            JIRA: The connected JIRA client

        Raises:
            ConnectionError: If not connected and connection fails
        """
        if self._client is None:
            self.connect()
        return self._client

    def connect(self) -> None:
        """Establish connection to the JIRA server.

        Raises:
            AuthenticationError: If authentication fails
            ConnectionError: If connection to server fails
        """
        logger.info(f"Connecting to JIRA server: {self.config.server_url}")

        options = {"server": self.config.server_url}

        try:
            self._client = JIRA(
                options=options,
                basic_auth=(self.config.username, self.config.password),
            )
            # Verify connection by fetching server info
            server_info = self._client.server_info()
            logger.info(
                f"Connected to JIRA server version: {server_info.get('version', 'unknown')}"
            )
        except JIRAError as e:
            if e.status_code == 401:
                logger.error("Authentication failed - check credentials")
                raise AuthenticationError(
                    "Authentication failed. Please check your username and password."
                ) from e
            elif e.status_code == 403:
                logger.error("Access forbidden - check permissions")
                raise AuthenticationError(
                    "Access forbidden. Please check your account permissions."
                ) from e
            else:
                logger.error(f"JIRA error: {e}")
                raise ConnectionError(f"Failed to connect to JIRA: {e}") from e
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Failed to connect to JIRA server: {e}") from e

    def disconnect(self) -> None:
        """Close the connection to the JIRA server."""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("Disconnected from JIRA server")

    def is_connected(self) -> bool:
        """Check if the client is connected.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._client is not None

    def search_issues(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 1000,
        fields: Optional[str] = None,
    ):
        """Search for issues using JQL.

        Args:
            jql: JQL query string
            start_at: Starting index for pagination
            max_results: Maximum number of results to return
            fields: Comma-separated list of fields to return (None for all)

        Returns:
            ResultList: List of matching issues
        """
        return self.client.search_issues(
            jql, startAt=start_at, maxResults=max_results, fields=fields
        )

    def get_issue(self, issue_key: str, expand: Optional[str] = None):
        """Get a specific issue by key.

        Args:
            issue_key: The issue key (e.g., "PROJ-123")
            expand: Comma-separated list of fields to expand

        Returns:
            Issue: The JIRA issue object
        """
        return self.client.issue(issue_key, expand=expand)

    def __enter__(self) -> "JiraClient":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()
