"""Changelog fetching and processing functionality."""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from jira_tools.client import JiraClient
from jira_tools.exceptions import FetchError

logger = logging.getLogger(__name__)


class ChangelogFetcher:
    """Fetches and processes JIRA issue changelogs into pandas DataFrames.

    This class provides methods to fetch changelog history for JIRA issues
    and convert them to DataFrames for analysis.

    Attributes:
        client: The JiraClient instance for API calls

    Example:
        >>> client = JiraClient(config)
        >>> fetcher = ChangelogFetcher(client)
        >>> df = fetcher.fetch_changelog("PROJ-123")
        >>> print(df.head())
    """

    def __init__(self, client: JiraClient) -> None:
        """Initialize the ChangelogFetcher.

        Args:
            client: A JiraClient instance for API calls
        """
        self.client = client
        logger.info("ChangelogFetcher initialized")

    def fetch_changelog(self, issue_key: str) -> pd.DataFrame:
        """Fetch changelog for a single issue.

        Args:
            issue_key: The JIRA issue key (e.g., "PROJ-123")

        Returns:
            pd.DataFrame: DataFrame containing changelog entries

        Raises:
            FetchError: If fetching changelog fails
        """
        logger.info(f"Fetching changelog for issue: {issue_key}")

        try:
            issue = self.client.get_issue(issue_key, expand="changelog")
            return self._changelog_to_dataframe(issue)
        except Exception as e:
            logger.error(f"Failed to fetch changelog for {issue_key}: {e}")
            raise FetchError(f"Failed to fetch changelog for {issue_key}: {e}") from e

    def fetch_changelogs_for_issues(
        self,
        issue_keys: List[str],
        show_progress: bool = True,
    ) -> pd.DataFrame:
        """Fetch changelogs for multiple issues.

        Args:
            issue_keys: List of JIRA issue keys
            show_progress: Whether to log progress (default: True)

        Returns:
            pd.DataFrame: Combined DataFrame with changelogs for all issues

        Raises:
            FetchError: If fetching changelogs fails
        """
        logger.info(f"Fetching changelogs for {len(issue_keys)} issues")

        all_records = []
        total = len(issue_keys)

        for idx, issue_key in enumerate(issue_keys):
            if show_progress and (idx + 1) % 10 == 0:
                logger.info(f"Progress: {idx + 1}/{total} issues processed")

            try:
                issue = self.client.get_issue(issue_key, expand="changelog")
                records = self._extract_changelog_records(issue)
                all_records.extend(records)
            except Exception as e:
                logger.warning(f"Failed to fetch changelog for {issue_key}: {e}")
                continue

        logger.info(f"Fetched {len(all_records)} changelog entries")

        if not all_records:
            return pd.DataFrame()

        return pd.DataFrame(all_records)

    def fetch_changelogs_for_project(
        self,
        project: str,
        jql_filter: Optional[str] = None,
        batch_size: int = 1000,
    ) -> pd.DataFrame:
        """Fetch changelogs for all issues in a project.

        Args:
            project: The JIRA project key
            jql_filter: Additional JQL filter (optional)
            batch_size: Number of issues to fetch per batch

        Returns:
            pd.DataFrame: Combined DataFrame with changelogs for all issues
        """
        # First, fetch all issue keys
        jql = f"project = '{project}'"
        if jql_filter:
            jql = f"{jql} AND {jql_filter}"

        logger.info(f"Fetching issue keys for project: {project}")

        issue_keys = []
        start_at = 0

        while True:
            issues = self.client.search_issues(
                jql, start_at=start_at, max_results=batch_size, fields="key"
            )

            if not issues:
                break

            issue_keys.extend([issue.key for issue in issues])

            if len(issues) < batch_size:
                break

            start_at += batch_size

        logger.info(f"Found {len(issue_keys)} issues in project {project}")

        if not issue_keys:
            return pd.DataFrame()

        return self.fetch_changelogs_for_issues(issue_keys)

    def _changelog_to_dataframe(self, issue: Any) -> pd.DataFrame:
        """Convert an issue's changelog to a DataFrame.

        Args:
            issue: JIRA issue object with expanded changelog

        Returns:
            pd.DataFrame: DataFrame with changelog entries
        """
        records = self._extract_changelog_records(issue)

        if not records:
            logger.debug(f"No changelog entries for issue {issue.key}")
            return pd.DataFrame()

        return pd.DataFrame(records)

    def _extract_changelog_records(self, issue: Any) -> List[Dict[str, Any]]:
        """Extract changelog records from an issue.

        Args:
            issue: JIRA issue object with expanded changelog

        Returns:
            List[Dict]: List of changelog entry dictionaries
        """
        records = []

        if not hasattr(issue, "changelog"):
            logger.warning(f"Issue {issue.key} has no changelog attribute")
            return records

        changelog = issue.changelog

        for history in changelog.histories:
            for item in history.items:
                record = {
                    "key": issue.key,
                    "author": str(history.author) if history.author else None,
                    "date": history.created,
                    "field": item.field,
                    "fieldtype": item.fieldtype,
                    # Use getattr because 'from' is a Python reserved keyword
                    "from_value": getattr(item, "from"),
                    "from_string": item.fromString,
                    "to_value": item.to,
                    "to_string": item.toString,
                }
                records.append(record)

        return records
