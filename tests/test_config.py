"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from jira_tools.config import Config
from jira_tools.exceptions import ConfigurationError


class TestConfig:
    """Tests for the Config class."""

    def test_config_creation_valid(self):
        """Test creating a valid config."""
        config = Config(
            server_url="https://jira.example.com",
            username="user",
            password="pass",
        )
        assert config.server_url == "https://jira.example.com"
        assert config.username == "user"
        assert config.password == "pass"
        assert config.project is None
        assert config.batch_size == 1000

    def test_config_with_all_options(self):
        """Test creating a config with all options."""
        config = Config(
            server_url="https://jira.example.com",
            username="user",
            password="pass",
            project="MYPROJ",
            batch_size=500,
        )
        assert config.project == "MYPROJ"
        assert config.batch_size == 500

    def test_config_strips_trailing_slash(self):
        """Test that trailing slash is removed from server URL."""
        config = Config(
            server_url="https://jira.example.com/",
            username="user",
            password="pass",
        )
        assert config.server_url == "https://jira.example.com"

    def test_config_missing_server_url(self):
        """Test that missing server URL raises error."""
        with pytest.raises(ConfigurationError, match="server URL"):
            Config(server_url="", username="user", password="pass")

    def test_config_missing_username(self):
        """Test that missing username raises error."""
        with pytest.raises(ConfigurationError, match="username"):
            Config(
                server_url="https://jira.example.com",
                username="",
                password="pass",
            )

    def test_config_missing_password(self):
        """Test that missing password raises error."""
        with pytest.raises(ConfigurationError, match="password"):
            Config(
                server_url="https://jira.example.com",
                username="user",
                password="",
            )

    def test_config_invalid_batch_size(self):
        """Test that invalid batch size raises error."""
        with pytest.raises(ConfigurationError, match="Batch size"):
            Config(
                server_url="https://jira.example.com",
                username="user",
                password="pass",
                batch_size=0,
            )

    def test_config_repr_hides_password(self):
        """Test that repr doesn't expose password."""
        config = Config(
            server_url="https://jira.example.com",
            username="user",
            password="supersecret",
        )
        repr_str = repr(config)
        assert "supersecret" not in repr_str
        assert "***" in repr_str

    def test_config_from_env(self):
        """Test loading config from environment variables."""
        env_vars = {
            "JIRA_SERVER_URL": "https://jira.test.com",
            "JIRA_USERNAME": "testuser",
            "JIRA_PASSWORD": "testpass",
            "JIRA_PROJECT": "TESTPROJ",
            "JIRA_BATCH_SIZE": "250",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.from_env()
            assert config.server_url == "https://jira.test.com"
            assert config.username == "testuser"
            assert config.password == "testpass"
            assert config.project == "TESTPROJ"
            assert config.batch_size == 250

    def test_config_from_env_missing_required(self):
        """Test that missing required env vars raises error."""
        env_vars = {
            "JIRA_SERVER_URL": "",
            "JIRA_USERNAME": "",
            "JIRA_PASSWORD": "",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            with pytest.raises(ConfigurationError):
                Config.from_env()

    def test_config_from_env_invalid_batch_size(self):
        """Test that invalid batch size in env uses default."""
        env_vars = {
            "JIRA_SERVER_URL": "https://jira.test.com",
            "JIRA_USERNAME": "testuser",
            "JIRA_PASSWORD": "testpass",
            "JIRA_BATCH_SIZE": "invalid",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.from_env()
            assert config.batch_size == 1000
