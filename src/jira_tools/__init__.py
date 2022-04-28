"""
JIRA Tools - A Python library for fetching and analyzing JIRA data.

This package provides tools to:
- Connect to JIRA servers with secure authentication
- Fetch issues from JIRA projects
- Retrieve changelog history for issues
- Convert JIRA data to pandas DataFrames for analysis
"""

from jira_tools.client import JiraClient
from jira_tools.issues import IssueFetcher
from jira_tools.changelog import ChangelogFetcher
from jira_tools.config import Config

__version__ = "1.0.0"
__all__ = ["JiraClient", "IssueFetcher", "ChangelogFetcher", "Config"]
