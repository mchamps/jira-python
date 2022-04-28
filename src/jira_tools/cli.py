"""Command-line interface for JIRA Tools."""

import argparse
import logging
import sys
from typing import Optional

from jira_tools.client import JiraClient
from jira_tools.config import Config
from jira_tools.issues import IssueFetcher
from jira_tools.changelog import ChangelogFetcher
from jira_tools.exceptions import JiraToolsError


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO level
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def fetch_issues_command(
    project: str,
    output: Optional[str] = None,
    jql_filter: Optional[str] = None,
    format: str = "csv",
) -> int:
    """Fetch issues from a JIRA project.

    Args:
        project: JIRA project key
        output: Output file path (stdout if None)
        jql_filter: Additional JQL filter
        format: Output format (csv, json, excel)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        config = Config.from_env()
        with JiraClient(config) as client:
            fetcher = IssueFetcher(client, batch_size=config.batch_size)
            df = fetcher.fetch_project_issues(project, jql_filter=jql_filter)

            if df.empty:
                print("No issues found.", file=sys.stderr)
                return 0

            if output:
                if format == "csv":
                    df.to_csv(output, index=False)
                elif format == "json":
                    df.to_json(output, orient="records", indent=2)
                elif format == "excel":
                    df.to_excel(output, index=False)
                print(f"Saved {len(df)} issues to {output}")
            else:
                print(df.to_string())

            return 0

    except JiraToolsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def fetch_changelog_command(
    project: str,
    output: Optional[str] = None,
    jql_filter: Optional[str] = None,
    format: str = "csv",
) -> int:
    """Fetch changelogs from a JIRA project.

    Args:
        project: JIRA project key
        output: Output file path (stdout if None)
        jql_filter: Additional JQL filter
        format: Output format (csv, json, excel)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        config = Config.from_env()
        with JiraClient(config) as client:
            fetcher = ChangelogFetcher(client)
            df = fetcher.fetch_changelogs_for_project(
                project,
                jql_filter=jql_filter,
                batch_size=config.batch_size,
            )

            if df.empty:
                print("No changelog entries found.", file=sys.stderr)
                return 0

            if output:
                if format == "csv":
                    df.to_csv(output, index=False)
                elif format == "json":
                    df.to_json(output, orient="records", indent=2)
                elif format == "excel":
                    df.to_excel(output, index=False)
                print(f"Saved {len(df)} changelog entries to {output}")
            else:
                print(df.to_string())

            return 0

    except JiraToolsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="jira-tools",
        description="Fetch and analyze JIRA data",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Issues command
    issues_parser = subparsers.add_parser("issues", help="Fetch project issues")
    issues_parser.add_argument("project", help="JIRA project key")
    issues_parser.add_argument(
        "-o", "--output",
        help="Output file path",
    )
    issues_parser.add_argument(
        "-f", "--filter",
        dest="jql_filter",
        help="Additional JQL filter",
    )
    issues_parser.add_argument(
        "--format",
        choices=["csv", "json", "excel"],
        default="csv",
        help="Output format (default: csv)",
    )

    # Changelog command
    changelog_parser = subparsers.add_parser("changelog", help="Fetch project changelog")
    changelog_parser.add_argument("project", help="JIRA project key")
    changelog_parser.add_argument(
        "-o", "--output",
        help="Output file path",
    )
    changelog_parser.add_argument(
        "-f", "--filter",
        dest="jql_filter",
        help="Additional JQL filter",
    )
    changelog_parser.add_argument(
        "--format",
        choices=["csv", "json", "excel"],
        default="csv",
        help="Output format (default: csv)",
    )

    return parser


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.command == "issues":
        return fetch_issues_command(
            project=args.project,
            output=args.output,
            jql_filter=args.jql_filter,
            format=args.format,
        )
    elif args.command == "changelog":
        return fetch_changelog_command(
            project=args.project,
            output=args.output,
            jql_filter=args.jql_filter,
            format=args.format,
        )
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
