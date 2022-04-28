# JIRA Tools

A Python library for fetching and analyzing JIRA data using pandas DataFrames.

## Features

- **Secure Authentication**: Environment variable-based credential management
- **Issue Fetching**: Fetch all issues from a JIRA project with automatic pagination
- **Changelog Tracking**: Retrieve complete changelog history for issues
- **DataFrame Output**: Convert JIRA data to pandas DataFrames for analysis
- **Error Handling**: Comprehensive error handling and logging
- **Type Hints**: Full type annotation support

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/jira-tools.git
cd jira-tools

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Dependencies

- Python 3.9+
- jira >= 3.5.0
- pandas >= 2.0.0
- python-dotenv >= 1.0.0

## Configuration

### Environment Variables

Create a `.env` file in your project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `JIRA_SERVER_URL` | Your JIRA server URL | `https://yourcompany.atlassian.net` |
| `JIRA_USERNAME` | Your JIRA username/email | `user@example.com` |
| `JIRA_PASSWORD` | Your JIRA API token | `your-api-token` |
| `JIRA_PROJECT` | Default project key (optional) | `MYPROJECT` |
| `JIRA_BATCH_SIZE` | Issues per request (optional) | `1000` |

> **Security Note**: Never commit your `.env` file. It's included in `.gitignore`.

### Getting a JIRA API Token

1. Log in to [Atlassian Account](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a descriptive name
4. Copy the token and use it as `JIRA_PASSWORD`

## Usage

### Basic Usage

```python
from jira_tools import JiraClient, IssueFetcher, ChangelogFetcher, Config

# Load configuration from environment
config = Config.from_env()

# Using context manager (recommended)
with JiraClient(config) as client:
    # Fetch all issues from a project
    issue_fetcher = IssueFetcher(client)
    issues_df = issue_fetcher.fetch_project_issues("MYPROJECT")
    print(f"Found {len(issues_df)} issues")

    # Fetch changelog for all issues
    changelog_fetcher = ChangelogFetcher(client)
    changelog_df = changelog_fetcher.fetch_changelogs_for_issues(
        issues_df["key"].tolist()
    )
    print(f"Found {len(changelog_df)} changelog entries")
```

### Manual Configuration

```python
from jira_tools import JiraClient, IssueFetcher, Config

# Create config manually
config = Config(
    server_url="https://yourcompany.atlassian.net",
    username="user@example.com",
    password="your-api-token",
    project="MYPROJECT",
    batch_size=500,
)

# Connect to JIRA
client = JiraClient(config)
client.connect()

try:
    fetcher = IssueFetcher(client)
    df = fetcher.fetch_project_issues("MYPROJECT")
    print(df.head())
finally:
    client.disconnect()
```

### Fetching Issues with Filters

```python
# Fetch only open bugs
df = fetcher.fetch_project_issues(
    "MYPROJECT",
    jql_filter="issuetype = Bug AND status != Closed"
)

# Fetch with custom JQL
df = fetcher.fetch_issues(
    "project = MYPROJECT AND created >= -30d ORDER BY created DESC"
)
```

### Fetching Changelog

```python
from jira_tools import ChangelogFetcher

changelog_fetcher = ChangelogFetcher(client)

# Fetch changelog for a single issue
single_changelog = changelog_fetcher.fetch_changelog("PROJ-123")

# Fetch changelogs for multiple issues
issue_keys = ["PROJ-123", "PROJ-124", "PROJ-125"]
changelogs = changelog_fetcher.fetch_changelogs_for_issues(issue_keys)

# Fetch changelogs for entire project
project_changelogs = changelog_fetcher.fetch_changelogs_for_project("MYPROJECT")
```

### Exporting Data

```python
# Export to CSV
issues_df.to_csv("issues.csv", index=False)

# Export to Excel
issues_df.to_excel("issues.xlsx", index=False)

# Export to JSON
issues_df.to_json("issues.json", orient="records", indent=2)
```

## Available Fields

### Issue Fields

| Field | Description |
|-------|-------------|
| `key` | Issue key (e.g., PROJ-123) |
| `summary` | Issue summary/title |
| `description` | Full description |
| `assignee` | Current assignee |
| `reporter` | Issue reporter |
| `creator` | Issue creator |
| `created` | Creation timestamp |
| `updated` | Last update timestamp |
| `status` | Current status |
| `priority` | Priority level |
| `issuetype` | Issue type (Bug, Story, etc.) |
| `resolution` | Resolution status |
| `resolutiondate` | Resolution timestamp |
| `components` | List of components |
| `fixVersions` | List of fix versions |

### Changelog Fields

| Field | Description |
|-------|-------------|
| `key` | Issue key |
| `author` | Change author |
| `date` | Change timestamp |
| `field` | Field that was changed |
| `fieldtype` | Type of field |
| `from_value` | Previous value |
| `from_string` | Previous value (string) |
| `to_value` | New value |
| `to_string` | New value (string) |

## Development

### Setup Development Environment

```bash
# Clone and install with dev dependencies
git clone https://github.com/yourusername/jira-tools.git
cd jira-tools
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=jira_tools --cov-report=html

# Run specific test file
pytest tests/test_issues.py
```

### Code Quality

```bash
# Run linter
ruff check src tests

# Run type checker
mypy src

# Format code
ruff format src tests
```

## Error Handling

The library provides custom exceptions for different error scenarios:

```python
from jira_tools.exceptions import (
    JiraToolsError,      # Base exception
    ConfigurationError,  # Configuration issues
    AuthenticationError, # Auth failures
    ConnectionError,     # Connection issues
    FetchError,          # Data fetching errors
)

try:
    config = Config.from_env()
    with JiraClient(config) as client:
        fetcher = IssueFetcher(client)
        df = fetcher.fetch_project_issues("MYPROJECT")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except FetchError as e:
    print(f"Failed to fetch data: {e}")
```

## Logging

Enable logging to see detailed operation information:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Now operations will log their progress
with JiraClient(config) as client:
    fetcher = IssueFetcher(client)
    df = fetcher.fetch_project_issues("MYPROJECT")
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
