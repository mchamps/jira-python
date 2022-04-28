"""Tests for changelog fetching."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from jira_tools.changelog import ChangelogFetcher
from jira_tools.exceptions import FetchError


@pytest.fixture
def mock_client():
    """Create a mock JIRA client."""
    return MagicMock()


def create_mock_issue_with_changelog(key, history_items=None):
    """Create a mock JIRA issue with changelog."""
    issue = MagicMock()
    issue.key = key

    if history_items is None:
        history_items = []

    histories = []
    for hist_data in history_items:
        history = MagicMock()
        history.author = MagicMock(__str__=lambda self: hist_data.get("author", "Test User"))
        history.created = hist_data.get("date", "2024-01-01T10:00:00.000+0000")

        items = []
        for item_data in hist_data.get("items", []):
            item = MagicMock()
            item.field = item_data.get("field", "status")
            item.fieldtype = item_data.get("fieldtype", "jira")
            # Use setattr for 'from' since it's a reserved keyword
            setattr(item, "from", item_data.get("from_value"))
            item.fromString = item_data.get("from_string", "Old Value")
            item.to = item_data.get("to_value")
            item.toString = item_data.get("to_string", "New Value")
            items.append(item)

        history.items = items
        histories.append(history)

    changelog = MagicMock()
    changelog.histories = histories
    issue.changelog = changelog

    return issue


class TestChangelogFetcher:
    """Tests for the ChangelogFetcher class."""

    def test_fetcher_initialization(self, mock_client):
        """Test fetcher initialization."""
        fetcher = ChangelogFetcher(mock_client)
        assert fetcher.client == mock_client

    def test_fetch_changelog_empty(self, mock_client):
        """Test fetching changelog with no history."""
        mock_issue = create_mock_issue_with_changelog("PROJ-1", [])
        mock_client.get_issue.return_value = mock_issue

        fetcher = ChangelogFetcher(mock_client)
        df = fetcher.fetch_changelog("PROJ-1")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_fetch_changelog_success(self, mock_client):
        """Test successfully fetching changelog."""
        history_items = [
            {
                "author": "John Doe",
                "date": "2024-01-15T10:00:00.000+0000",
                "items": [
                    {
                        "field": "status",
                        "from_string": "Open",
                        "to_string": "In Progress",
                    }
                ],
            }
        ]
        mock_issue = create_mock_issue_with_changelog("PROJ-1", history_items)
        mock_client.get_issue.return_value = mock_issue

        fetcher = ChangelogFetcher(mock_client)
        df = fetcher.fetch_changelog("PROJ-1")

        assert len(df) == 1
        assert df.iloc[0]["key"] == "PROJ-1"
        assert df.iloc[0]["field"] == "status"
        assert df.iloc[0]["from_string"] == "Open"
        assert df.iloc[0]["to_string"] == "In Progress"

    def test_fetch_changelog_multiple_changes(self, mock_client):
        """Test fetching changelog with multiple changes."""
        history_items = [
            {
                "items": [
                    {"field": "status", "from_string": "Open", "to_string": "In Progress"},
                    {"field": "assignee", "from_string": "User A", "to_string": "User B"},
                ]
            },
            {
                "items": [
                    {"field": "status", "from_string": "In Progress", "to_string": "Done"},
                ]
            },
        ]
        mock_issue = create_mock_issue_with_changelog("PROJ-1", history_items)
        mock_client.get_issue.return_value = mock_issue

        fetcher = ChangelogFetcher(mock_client)
        df = fetcher.fetch_changelog("PROJ-1")

        assert len(df) == 3  # 2 items in first history + 1 in second

    def test_fetch_changelog_error(self, mock_client):
        """Test error handling when fetching changelog."""
        mock_client.get_issue.side_effect = Exception("API Error")

        fetcher = ChangelogFetcher(mock_client)
        with pytest.raises(FetchError, match="Failed to fetch changelog"):
            fetcher.fetch_changelog("PROJ-1")

    def test_fetch_changelogs_for_issues(self, mock_client):
        """Test fetching changelogs for multiple issues."""
        issue1 = create_mock_issue_with_changelog("PROJ-1", [
            {"items": [{"field": "status"}]}
        ])
        issue2 = create_mock_issue_with_changelog("PROJ-2", [
            {"items": [{"field": "priority"}]}
        ])
        mock_client.get_issue.side_effect = [issue1, issue2]

        fetcher = ChangelogFetcher(mock_client)
        df = fetcher.fetch_changelogs_for_issues(["PROJ-1", "PROJ-2"])

        assert len(df) == 2
        assert set(df["key"]) == {"PROJ-1", "PROJ-2"}

    def test_fetch_changelogs_for_issues_handles_errors(self, mock_client):
        """Test that errors for individual issues are handled gracefully."""
        issue1 = create_mock_issue_with_changelog("PROJ-1", [
            {"items": [{"field": "status"}]}
        ])
        mock_client.get_issue.side_effect = [
            issue1,
            Exception("Issue not found"),
        ]

        fetcher = ChangelogFetcher(mock_client)
        # Should not raise, should skip the failed issue
        df = fetcher.fetch_changelogs_for_issues(
            ["PROJ-1", "PROJ-2"], show_progress=False
        )

        assert len(df) == 1
        assert df.iloc[0]["key"] == "PROJ-1"

    def test_fetch_changelogs_for_project(self, mock_client):
        """Test fetching changelogs for an entire project."""
        # First call for issue keys
        mock_issues = [MagicMock(key="PROJ-1"), MagicMock(key="PROJ-2")]
        mock_client.search_issues.return_value = mock_issues

        # Then calls for individual changelogs
        issue1 = create_mock_issue_with_changelog("PROJ-1", [
            {"items": [{"field": "status"}]}
        ])
        issue2 = create_mock_issue_with_changelog("PROJ-2", [
            {"items": [{"field": "priority"}]}
        ])
        mock_client.get_issue.side_effect = [issue1, issue2]

        fetcher = ChangelogFetcher(mock_client)
        df = fetcher.fetch_changelogs_for_project("PROJ")

        assert len(df) == 2
        mock_client.search_issues.assert_called()

    def test_fetch_changelogs_for_empty_project(self, mock_client):
        """Test fetching changelogs for a project with no issues."""
        mock_client.search_issues.return_value = []

        fetcher = ChangelogFetcher(mock_client)
        df = fetcher.fetch_changelogs_for_project("EMPTY")

        assert len(df) == 0

    def test_changelog_record_fields(self, mock_client):
        """Test that changelog records contain all expected fields."""
        history_items = [
            {
                "author": "Test User",
                "date": "2024-01-15T10:00:00.000+0000",
                "items": [
                    {
                        "field": "status",
                        "fieldtype": "jira",
                        "from_value": "1",
                        "from_string": "Open",
                        "to_value": "2",
                        "to_string": "Closed",
                    }
                ],
            }
        ]
        mock_issue = create_mock_issue_with_changelog("PROJ-1", history_items)
        mock_client.get_issue.return_value = mock_issue

        fetcher = ChangelogFetcher(mock_client)
        df = fetcher.fetch_changelog("PROJ-1")

        expected_columns = [
            "key", "author", "date", "field", "fieldtype",
            "from_value", "from_string", "to_value", "to_string"
        ]
        for col in expected_columns:
            assert col in df.columns

    def test_issue_without_changelog_attribute(self, mock_client):
        """Test handling issues without changelog attribute."""
        mock_issue = MagicMock()
        mock_issue.key = "PROJ-1"
        del mock_issue.changelog  # Remove changelog attribute
        mock_client.get_issue.return_value = mock_issue

        fetcher = ChangelogFetcher(mock_client)
        records = fetcher._extract_changelog_records(mock_issue)

        assert records == []
