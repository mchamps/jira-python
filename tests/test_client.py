"""Tests for JIRA client."""

from unittest.mock import MagicMock, patch

import pytest

from jira_tools.client import JiraClient
from jira_tools.config import Config
from jira_tools.exceptions import AuthenticationError, ConnectionError


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        server_url="https://jira.example.com",
        username="testuser",
        password="testpass",
    )


class TestJiraClient:
    """Tests for the JiraClient class."""

    def test_client_initialization(self, config):
        """Test client initialization."""
        client = JiraClient(config)
        assert client.config == config
        assert not client.is_connected()

    def test_client_not_connected_initially(self, config):
        """Test that client is not connected after initialization."""
        client = JiraClient(config)
        assert not client.is_connected()

    @patch("jira_tools.client.JIRA")
    def test_client_connect_success(self, mock_jira_class, config):
        """Test successful connection."""
        mock_jira = MagicMock()
        mock_jira.server_info.return_value = {"version": "9.0.0"}
        mock_jira_class.return_value = mock_jira

        client = JiraClient(config)
        client.connect()

        assert client.is_connected()
        mock_jira_class.assert_called_once()

    @patch("jira_tools.client.JIRA")
    def test_client_connect_auth_failure(self, mock_jira_class, config):
        """Test connection with authentication failure."""
        from jira.exceptions import JIRAError

        mock_jira_class.side_effect = JIRAError(status_code=401, text="Unauthorized")

        client = JiraClient(config)
        with pytest.raises(AuthenticationError):
            client.connect()

    @patch("jira_tools.client.JIRA")
    def test_client_connect_forbidden(self, mock_jira_class, config):
        """Test connection with forbidden error."""
        from jira.exceptions import JIRAError

        mock_jira_class.side_effect = JIRAError(status_code=403, text="Forbidden")

        client = JiraClient(config)
        with pytest.raises(AuthenticationError):
            client.connect()

    @patch("jira_tools.client.JIRA")
    def test_client_connect_other_error(self, mock_jira_class, config):
        """Test connection with other JIRA error."""
        from jira.exceptions import JIRAError

        mock_jira_class.side_effect = JIRAError(status_code=500, text="Server Error")

        client = JiraClient(config)
        with pytest.raises(ConnectionError):
            client.connect()

    @patch("jira_tools.client.JIRA")
    def test_client_connect_network_error(self, mock_jira_class, config):
        """Test connection with network error."""
        mock_jira_class.side_effect = Exception("Network unreachable")

        client = JiraClient(config)
        with pytest.raises(ConnectionError):
            client.connect()

    @patch("jira_tools.client.JIRA")
    def test_client_disconnect(self, mock_jira_class, config):
        """Test disconnection."""
        mock_jira = MagicMock()
        mock_jira.server_info.return_value = {"version": "9.0.0"}
        mock_jira_class.return_value = mock_jira

        client = JiraClient(config)
        client.connect()
        assert client.is_connected()

        client.disconnect()
        assert not client.is_connected()
        mock_jira.close.assert_called_once()

    @patch("jira_tools.client.JIRA")
    def test_client_context_manager(self, mock_jira_class, config):
        """Test using client as context manager."""
        mock_jira = MagicMock()
        mock_jira.server_info.return_value = {"version": "9.0.0"}
        mock_jira_class.return_value = mock_jira

        with JiraClient(config) as client:
            assert client.is_connected()

        mock_jira.close.assert_called_once()

    @patch("jira_tools.client.JIRA")
    def test_client_search_issues(self, mock_jira_class, config):
        """Test searching issues."""
        mock_jira = MagicMock()
        mock_jira.server_info.return_value = {"version": "9.0.0"}
        mock_jira.search_issues.return_value = []
        mock_jira_class.return_value = mock_jira

        client = JiraClient(config)
        client.connect()
        client.search_issues("project = TEST", start_at=0, max_results=100)

        mock_jira.search_issues.assert_called_once_with(
            "project = TEST", startAt=0, maxResults=100, fields=None
        )

    @patch("jira_tools.client.JIRA")
    def test_client_get_issue(self, mock_jira_class, config):
        """Test getting a specific issue."""
        mock_jira = MagicMock()
        mock_jira.server_info.return_value = {"version": "9.0.0"}
        mock_jira_class.return_value = mock_jira

        client = JiraClient(config)
        client.connect()
        client.get_issue("TEST-123", expand="changelog")

        mock_jira.issue.assert_called_once_with("TEST-123", expand="changelog")

    @patch("jira_tools.client.JIRA")
    def test_client_property_auto_connects(self, mock_jira_class, config):
        """Test that accessing client property auto-connects."""
        mock_jira = MagicMock()
        mock_jira.server_info.return_value = {"version": "9.0.0"}
        mock_jira_class.return_value = mock_jira

        client = JiraClient(config)
        assert not client.is_connected()

        # Accessing the client property should trigger connection
        _ = client.client

        assert client.is_connected()
