"""Issue fetching and processing functionality."""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from jira_tools.client import JiraClient
from jira_tools.exceptions import FetchError

logger = logging.getLogger(__name__)


class IssueFetcher:
    """Fetches and processes JIRA issues into pandas DataFrames.

    This class provides methods to fetch all issues from a JIRA project
    with automatic pagination and convert them to DataFrames for analysis.

    Attributes:
        client: The JiraClient instance for API calls
        batch_size: Number of issues to fetch per request

    Example:
        >>> client = JiraClient(config)
        >>> fetcher = IssueFetcher(client)
        >>> df = fetcher.fetch_project_issues("MYPROJECT")
        >>> print(df.head())
    """

    # Default fields to extract from issues
    DEFAULT_FIELDS = [
        "key",
        "assignee",
        "creator",
        "reporter",
        "created",
        "components",
        "description",
        "summary",
        "fixVersions",
        "issuetype",
        "priority",
        "resolution",
        "resolutiondate",
        "status",
        "updated",
    ]

    def __init__(self, client: JiraClient, batch_size: int = 1000) -> None:
        """Initialize the IssueFetcher.

        Args:
            client: A JiraClient instance for API calls
            batch_size: Number of issues to fetch per request (default: 1000)
        """
        self.client = client
        self.batch_size = batch_size
        logger.info(f"IssueFetcher initialized with batch_size={batch_size}")

    def fetch_project_issues(
        self,
        project: str,
        jql_filter: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Fetch all issues from a JIRA project.

        Args:
            project: The JIRA project key (e.g., "MYPROJECT")
            jql_filter: Additional JQL filter to apply (optional)
            fields: List of fields to extract (optional, uses defaults if None)

        Returns:
            pd.DataFrame: DataFrame containing all issues with specified fields

        Raises:
            FetchError: If fetching issues fails
        """
        jql = f"project = '{project}'"
        if jql_filter:
            jql = f"{jql} AND {jql_filter}"

        logger.info(f"Fetching issues with JQL: {jql}")
        return self.fetch_issues(jql, fields)

    def fetch_issues(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Fetch issues matching a JQL query.

        Args:
            jql: JQL query string
            fields: List of fields to extract (optional, uses defaults if None)

        Returns:
            pd.DataFrame: DataFrame containing all matching issues

        Raises:
            FetchError: If fetching issues fails
        """
        all_issues = self._fetch_all_issues(jql)
        logger.info(f"Fetched {len(all_issues)} issues")

        if not all_issues:
            logger.warning("No issues found matching the query")
            return pd.DataFrame()

        return self._issues_to_dataframe(all_issues, fields)

    def _fetch_all_issues(self, jql: str) -> List[Any]:
        """Fetch all issues matching a JQL query with pagination.

        Args:
            jql: JQL query string

        Returns:
            List: List of all JIRA issue objects

        Raises:
            FetchError: If fetching fails
        """
        all_issues = []
        start_at = 0

        try:
            while True:
                logger.debug(
                    f"Fetching issues starting at {start_at} "
                    f"(batch size: {self.batch_size})"
                )

                issues = self.client.search_issues(
                    jql, start_at=start_at, max_results=self.batch_size
                )

                if not issues:
                    break

                all_issues.extend(issues)
                logger.debug(f"Fetched {len(issues)} issues, total: {len(all_issues)}")

                if len(issues) < self.batch_size:
                    break

                start_at += self.batch_size

        except Exception as e:
            logger.error(f"Failed to fetch issues: {e}")
            raise FetchError(f"Failed to fetch issues: {e}") from e

        return all_issues

    def _issues_to_dataframe(
        self,
        issues: List[Any],
        fields: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Convert a list of JIRA issues to a pandas DataFrame.

        Args:
            issues: List of JIRA issue objects
            fields: List of fields to extract (uses defaults if None)

        Returns:
            pd.DataFrame: DataFrame with extracted fields
        """
        if fields is None:
            fields = self.DEFAULT_FIELDS

        records = []
        for issue in issues:
            record = self._extract_issue_fields(issue, fields)
            records.append(record)

        df = pd.DataFrame(records)
        logger.debug(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        return df

    def _extract_issue_fields(
        self,
        issue: Any,
        fields: List[str],
    ) -> Dict[str, Any]:
        """Extract specified fields from a JIRA issue.

        Args:
            issue: JIRA issue object
            fields: List of field names to extract

        Returns:
            Dict: Dictionary of field names to values
        """
        record = {}

        for field in fields:
            try:
                value = self._get_field_value(issue, field)
                record[field] = value
            except Exception as e:
                logger.debug(f"Could not extract field '{field}': {e}")
                record[field] = None

        return record

    def _get_field_value(self, issue: Any, field: str) -> Any:
        """Get the value of a specific field from an issue.

        Args:
            issue: JIRA issue object
            field: Field name to extract

        Returns:
            The field value, possibly processed for nested fields
        """
        if field == "key":
            return issue.key

        issue_fields = issue.fields

        # Handle nested fields
        field_mapping = {
            "assignee": lambda f: str(f.assignee) if f.assignee else None,
            "creator": lambda f: str(f.creator) if f.creator else None,
            "reporter": lambda f: str(f.reporter) if f.reporter else None,
            "created": lambda f: f.created,
            "components": lambda f: [str(c) for c in f.components] if f.components else [],
            "description": lambda f: f.description,
            "summary": lambda f: f.summary,
            "fixVersions": lambda f: [str(v) for v in f.fixVersions] if f.fixVersions else [],
            "issuetype": lambda f: f.issuetype.name if f.issuetype else None,
            "subtask": lambda f: f.issuetype.subtask if f.issuetype else None,
            "priority": lambda f: f.priority.name if f.priority else None,
            "resolution": lambda f: str(f.resolution) if f.resolution else None,
            "resolutiondate": lambda f: f.resolutiondate,
            "status": lambda f: f.status.name if f.status else None,
            "status_description": lambda f: f.status.description if f.status else None,
            "updated": lambda f: f.updated,
        }

        if field in field_mapping:
            return field_mapping[field](issue_fields)

        # Try direct attribute access for unknown fields
        return getattr(issue_fields, field, None)
