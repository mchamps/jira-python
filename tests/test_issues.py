"""Tests for issue fetching."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from jira_tools.config import Config
from jira_tools.issues import IssueFetcher
from jira_tools.exceptions import FetchError


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        server_url="https://jira.example.com",
        username="testuser",
        password="testpass",
    )


@pytest.fixture
def mock_client():
    """Create a mock JIRA client."""
    client = MagicMock()
    return client


def create_mock_issue(key, summary="Test Summary", status="Open"):
    """Create a mock JIRA issue."""
    issue = MagicMock()
    issue.key = key

    fields = MagicMock()
    fields.summary = summary
    fields.description = "Test description"
    fields.assignee = MagicMock(__str__=lambda self: "Test User")
    fields.creator = MagicMock(__str__=lambda self: "Creator User")
    fields.reporter = MagicMock(__str__=lambda self: "Reporter User")
    fields.created = "2024-01-01T10:00:00.000+0000"
    fields.updated = "2024-01-02T10:00:00.000+0000"
    fields.components = []
    fields.fixVersions = []
    fields.issuetype = MagicMock(name="Bug", subtask=False)
    fields.priority = MagicMock(name="High")
    fields.resolution = None
    fields.resolutiondate = None
    fields.status = MagicMock(name=status, description="Status description")

    issue.fields = fields
    return issue


class TestIssueFetcher:
    """Tests for the IssueFetcher class."""

    def test_fetcher_initialization(self, mock_client):
        """Test fetcher initialization."""
        fetcher = IssueFetcher(mock_client)
        assert fetcher.client == mock_client
        assert fetcher.batch_size == 1000

    def test_fetcher_custom_batch_size(self, mock_client):
        """Test fetcher with custom batch size."""
        fetcher = IssueFetcher(mock_client, batch_size=500)
        assert fetcher.batch_size == 500

    def test_fetch_project_issues_empty(self, mock_client):
        """Test fetching from empty project."""
        mock_client.search_issues.return_value = []

        fetcher = IssueFetcher(mock_client)
        df = fetcher.fetch_project_issues("EMPTY")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        mock_client.search_issues.assert_called()

    def test_fetch_project_issues_success(self, mock_client):
        """Test successfully fetching project issues."""
        mock_issues = [
            create_mock_issue("PROJ-1", "Issue 1"),
            create_mock_issue("PROJ-2", "Issue 2"),
        ]
        mock_client.search_issues.return_value = mock_issues

        fetcher = IssueFetcher(mock_client)
        df = fetcher.fetch_project_issues("PROJ")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "key" in df.columns
        assert "summary" in df.columns

    def test_fetch_project_issues_with_filter(self, mock_client):
        """Test fetching with additional JQL filter."""
        mock_client.search_issues.return_value = []

        fetcher = IssueFetcher(mock_client)
        fetcher.fetch_project_issues("PROJ", jql_filter="status = Open")

        # Verify the JQL was constructed correctly
        call_args = mock_client.search_issues.call_args
        jql = call_args[0][0]
        assert "project = 'PROJ'" in jql
        assert "status = Open" in jql

    def test_fetch_issues_pagination(self, mock_client):
        """Test that pagination works correctly."""
        # First call returns full batch, second call returns empty
        batch1 = [create_mock_issue(f"PROJ-{i}") for i in range(1000)]
        batch2 = []
        mock_client.search_issues.side_effect = [batch1, batch2]

        fetcher = IssueFetcher(mock_client, batch_size=1000)
        df = fetcher.fetch_project_issues("PROJ")

        assert len(df) == 1000
        assert mock_client.search_issues.call_count == 2

    def test_fetch_issues_pagination_partial_last_batch(self, mock_client):
        """Test pagination with partial last batch."""
        batch1 = [create_mock_issue(f"PROJ-{i}") for i in range(100)]
        batch2 = [create_mock_issue(f"PROJ-{i}") for i in range(100, 150)]
        mock_client.search_issues.side_effect = [batch1, batch2]

        fetcher = IssueFetcher(mock_client, batch_size=100)
        df = fetcher.fetch_project_issues("PROJ")

        assert len(df) == 150
        # Should stop after batch2 since it's less than batch_size
        assert mock_client.search_issues.call_count == 2

    def test_fetch_issues_error_handling(self, mock_client):
        """Test error handling during fetch."""
        mock_client.search_issues.side_effect = Exception("API Error")

        fetcher = IssueFetcher(mock_client)
        with pytest.raises(FetchError, match="Failed to fetch"):
            fetcher.fetch_project_issues("PROJ")

    def test_extract_issue_fields(self, mock_client):
        """Test extracting fields from an issue."""
        mock_issue = create_mock_issue("PROJ-1", "Test Summary", "In Progress")

        fetcher = IssueFetcher(mock_client)
        record = fetcher._extract_issue_fields(mock_issue, ["key", "summary", "status"])

        assert record["key"] == "PROJ-1"
        assert record["summary"] == "Test Summary"
        assert record["status"] == "In Progress"

    def test_extract_issue_fields_handles_missing(self, mock_client):
        """Test that missing fields don't cause errors."""
        mock_issue = create_mock_issue("PROJ-1")
        mock_issue.fields.nonexistent = None

        fetcher = IssueFetcher(mock_client)
        record = fetcher._extract_issue_fields(
            mock_issue, ["key", "nonexistent_field"]
        )

        assert record["key"] == "PROJ-1"
        assert record["nonexistent_field"] is None

    def test_default_fields(self, mock_client):
        """Test that default fields are used when none specified."""
        mock_issues = [create_mock_issue("PROJ-1")]
        mock_client.search_issues.return_value = mock_issues

        fetcher = IssueFetcher(mock_client)
        df = fetcher.fetch_project_issues("PROJ")

        # Check that default fields are present
        for field in ["key", "summary", "status", "priority"]:
            assert field in df.columns

    def test_custom_fields(self, mock_client):
        """Test fetching with custom fields."""
        mock_issues = [create_mock_issue("PROJ-1")]
        mock_client.search_issues.return_value = mock_issues

        fetcher = IssueFetcher(mock_client)
        df = fetcher.fetch_issues("project = PROJ", fields=["key", "summary"])

        assert "key" in df.columns
        assert "summary" in df.columns
        # Other default fields should not be present
        assert len(df.columns) == 2
