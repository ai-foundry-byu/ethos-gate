"""Tests for ethos_gate.hooks.credential_scrape."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ethos_gate.hooks.credential_scrape import evaluate, ALLOW, Verdict


class TestUniversalBlocks:
    def test_keychain_dump_blocked(self):
        v = evaluate("Bash", {"command": "security dump-keychain"})
        assert v.blocked

    def test_browser_login_db_bash_blocked(self):
        v = evaluate("Bash", {"command": "sqlite3 'Login Data'"})
        assert v.blocked

    def test_browser_login_path_blocked(self):
        v = evaluate("Read", {"file_path": "/Users/someone/Chrome/Default/Login Data"})
        assert v.blocked

    def test_password_manager_blocked(self):
        v = evaluate("Bash", {"command": "op item get my-password"})
        assert v.blocked

    def test_safe_bash_allowed(self):
        v = evaluate("Bash", {"command": "ls -la ~/projects"})
        assert not v.blocked

    def test_git_status_allowed(self):
        v = evaluate("Bash", {"command": "git status"})
        assert not v.blocked


class TestStrictBlocks:
    def test_crontab_edit_blocked_in_strict(self):
        v = evaluate("Bash", {"command": "crontab -e"}, strict=True)
        assert v.blocked

    def test_crontab_list_blocked_in_strict(self):
        v = evaluate("Bash", {"command": "crontab -l"}, strict=True)
        assert v.blocked

    def test_crontab_allowed_in_non_strict(self):
        v = evaluate("Bash", {"command": "crontab -l"}, strict=False)
        assert not v.blocked

    def test_launchctl_blocked_in_strict(self):
        v = evaluate("Bash", {"command": "launchctl load ~/Library/LaunchAgents/com.example.plist"}, strict=True)
        assert v.blocked

    def test_launchctl_allowed_in_non_strict(self):
        v = evaluate("Bash", {"command": "launchctl load ~/Library/LaunchAgents/com.example.plist"}, strict=False)
        assert not v.blocked


class TestSandboxBlocks:
    def test_env_file_read_blocked_in_sandbox(self):
        v = evaluate("Read", {"file_path": "/project/.env"}, sandbox=True)
        assert v.blocked

    def test_env_file_read_allowed_outside_sandbox(self):
        v = evaluate("Read", {"file_path": "/project/.env"}, sandbox=False)
        assert not v.blocked

    def test_env_example_always_allowed(self):
        v = evaluate("Read", {"file_path": "/project/.env.example"}, sandbox=True)
        assert not v.blocked

    def test_env_sample_always_allowed(self):
        v = evaluate("Read", {"file_path": "/project/.env.sample"}, sandbox=True)
        assert not v.blocked

    def test_private_key_blocked_in_sandbox(self):
        v = evaluate("Read", {"file_path": "/home/user/.ssh/id_rsa"}, sandbox=True)
        assert v.blocked

    def test_aws_credentials_blocked_in_sandbox(self):
        v = evaluate("Read", {"file_path": "/home/user/.aws/credentials"}, sandbox=True)
        assert v.blocked

    def test_normal_file_allowed_in_sandbox(self):
        v = evaluate("Read", {"file_path": "/project/src/app.py"}, sandbox=True)
        assert not v.blocked

    def test_cat_env_blocked_in_sandbox(self):
        v = evaluate("Bash", {"command": "cat .env"}, sandbox=True)
        assert v.blocked

    def test_cat_env_allowed_outside_sandbox(self):
        v = evaluate("Bash", {"command": "cat .env"}, sandbox=False)
        assert not v.blocked


class TestNonBashTools:
    def test_websearch_always_allowed(self):
        v = evaluate("WebSearch", {"query": "foo"})
        assert not v.blocked

    def test_webfetch_always_allowed(self):
        v = evaluate("WebFetch", {"url": "https://example.com"})
        assert not v.blocked

    def test_edit_with_safe_path_allowed(self):
        v = evaluate("Edit", {"file_path": "/project/src/main.py"})
        assert not v.blocked

    def test_edit_with_env_path_blocked_in_sandbox(self):
        v = evaluate("Edit", {"file_path": "/project/.env"}, sandbox=True)
        assert v.blocked
