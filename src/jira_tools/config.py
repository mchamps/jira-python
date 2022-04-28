"""Configuration management for JIRA Tools.

This module handles loading configuration from environment variables
and provides secure credential management.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional

from jira_tools.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration container for JIRA connection settings.

    Attributes:
        server_url: The JIRA server URL (e.g., https://jira.atlassian.com)
        username: JIRA username for authentication
        password: JIRA password or API token for authentication
        project: Default JIRA project key (optional)
        batch_size: Number of issues to fetch per request (default: 1000)
    """

    server_url: str
    username: str
    password: str
    project: Optional[str] = None
    batch_size: int = 1000

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.server_url:
            raise ConfigurationError("JIRA server URL is required")
        if not self.username:
            raise ConfigurationError("JIRA username is required")
        if not self.password:
            raise ConfigurationError("JIRA password/token is required")

        # Ensure server URL doesn't have trailing slash
        self.server_url = self.server_url.rstrip("/")

        # Validate batch size
        if self.batch_size <= 0:
            raise ConfigurationError("Batch size must be a positive integer")

    @classmethod
    def from_env(cls) -> "Config":
        """Create a Config instance from environment variables.

        Environment Variables:
            JIRA_SERVER_URL: The JIRA server URL
            JIRA_USERNAME: JIRA username
            JIRA_PASSWORD: JIRA password or API token
            JIRA_PROJECT: Default project key (optional)
            JIRA_BATCH_SIZE: Batch size for fetching issues (optional, default: 1000)

        Returns:
            Config: A configured Config instance

        Raises:
            ConfigurationError: If required environment variables are missing
        """
        server_url = os.environ.get("JIRA_SERVER_URL", "")
        username = os.environ.get("JIRA_USERNAME", "")
        password = os.environ.get("JIRA_PASSWORD", "")
        project = os.environ.get("JIRA_PROJECT")
        batch_size_str = os.environ.get("JIRA_BATCH_SIZE", "1000")

        try:
            batch_size = int(batch_size_str)
        except ValueError:
            logger.warning(
                f"Invalid JIRA_BATCH_SIZE '{batch_size_str}', using default 1000"
            )
            batch_size = 1000

        return cls(
            server_url=server_url,
            username=username,
            password=password,
            project=project,
            batch_size=batch_size,
        )

    def __repr__(self) -> str:
        """Return a string representation without exposing credentials."""
        return (
            f"Config(server_url='{self.server_url}', "
            f"username='{self.username}', "
            f"password='***', "
            f"project='{self.project}', "
            f"batch_size={self.batch_size})"
        )
