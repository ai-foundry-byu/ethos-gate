"""Tests for ethos_gate.audit.trifecta."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ethos_gate.audit.trifecta import (
    Leg,
    grade_agent,
    run_audit,
    AuditResult,
    AgentProfile,
)


TRIFECTA_TEXT = """
# Example trifecta agent
# Leg 1: reads credentials and vault
api_key = vault.get("secret")

# Leg 2: fetches external email/web content
def process(inbox):
    for msg in gmail.search("from:unknown"):
        text = webfetch(msg.url)

# Leg 3: sends outbound email
send_email(to="user@external.com", body=text)
"""

SINGLE_LEG_TEXT = """
# Only has Leg 1 — reads secrets
api_key = credentials.get("MY_KEY")
"""

CLEAN_TEXT = """
# No sensitive legs
def add(a, b):
    return a + b
"""


def _write_temp(text: str, suffix: str = ".py") -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    f.write(text)
    f.flush()
    f.close()
    return Path(f.name)


class TestLegScanner:
    def test_trifecta_all_three(self):
        l1, l2, l3 = Leg.scan(TRIFECTA_TEXT)
        assert l1 and l2 and l3

    def test_single_leg_only_leg1(self):
        l1, l2, l3 = Leg.scan(SINGLE_LEG_TEXT)
        assert l1
        assert not l2
        assert not l3

    def test_clean_no_legs(self):
        l1, l2, l3 = Leg.scan(CLEAN_TEXT)
        assert not l1
        assert not l2
        assert not l3

    def test_outbound_email_detected(self):
        _, _, l3 = Leg.scan("send_email(to='bob@example.com', body=text)")
        assert l3

    def test_websearch_detected(self):
        _, l2, _ = Leg.scan("results = webfetch('https://example.com')")
        assert l2

    def test_api_key_detected(self):
        l1, _, _ = Leg.scan("api_key = os.environ.get('SECRET_KEY')")
        assert l1


class TestGradeAgent:
    def test_trifecta_agent_has_all_legs(self):
        path = _write_temp(TRIFECTA_TEXT)
        try:
            profile = grade_agent(path)
            assert profile is not None
            assert profile.has_all_legs
            assert len(profile.legs) == 3
        finally:
            path.unlink()

    def test_clean_agent_has_no_legs(self):
        path = _write_temp(CLEAN_TEXT)
        try:
            profile = grade_agent(path)
            assert profile is not None
            assert not profile.has_all_legs
        finally:
            path.unlink()

    def test_missing_file_returns_none(self):
        profile = grade_agent(Path("/nonexistent/file.py"))
        assert profile is None


class TestRunAudit:
    def test_finds_trifecta_in_dir(self, tmp_path):
        (tmp_path / "agent_trifecta.py").write_text(TRIFECTA_TEXT)
        (tmp_path / "agent_clean.py").write_text(CLEAN_TEXT)

        result = run_audit([str(tmp_path)])
        assert len(result.trifecta_agents) == 1
        assert result.trifecta_agents[0].name == "agent_trifecta"

    def test_no_findings_on_clean_dir(self, tmp_path):
        (tmp_path / "util.py").write_text(CLEAN_TEXT)
        result = run_audit([str(tmp_path)])
        assert len(result.trifecta_agents) == 0

    def test_audit_result_summary(self, tmp_path):
        (tmp_path / "agent_x.py").write_text(TRIFECTA_TEXT)
        result = run_audit([str(tmp_path)])
        summary = result.summary()
        assert summary["trifecta_count"] == 1
        assert len(summary["trifecta_agents"]) == 1

    def test_nonexistent_path_not_blind(self, tmp_path):
        # A non-existent file is simply skipped (no agents, no blind paths)
        # because _iter_agent_files only yields existing files.
        result = run_audit([str(tmp_path / "does_not_exist.py")])
        assert len(result.agents) == 0
        assert not result.is_blind
