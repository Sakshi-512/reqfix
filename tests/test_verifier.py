"""Tests for core.verifier.Verifier."""

import subprocess

from core.fixer import FixSuggestion
from core.verifier import Verifier


def _suggestion(name: str, version: str) -> FixSuggestion:
    return FixSuggestion(
        package_name=name,
        original_specifier=f"=={version}",
        suggested_version=version,
        fixed_line=f"{name}=={version}",
        reason="test",
        was_conflict=False,
        was_unpinned=False,
    )


def test_verify_success_when_pip_returncode_zero(monkeypatch):
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = Verifier().verify([_suggestion("flask", "3.0.0")])

    assert result.success is True
    assert result.conflicts == []


def test_verify_failure_parses_stderr_conflicts(monkeypatch):
    stderr = (
        "ERROR: ResolutionImpossible: for help visit "
        "https://pip.pypa.io/en/latest/topics/dependency-resolution/"
    )

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr=stderr
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = Verifier().verify(
        [_suggestion("requests", "2.28.1"), _suggestion("urllib3", "2.2.0")]
    )

    assert result.success is False
    assert len(result.conflicts) >= 1
    assert any("ResolutionImpossible" in line for line in result.conflicts)


def test_verify_timeout_returns_failure(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=120)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = Verifier().verify([_suggestion("flask", "3.0.0")])

    assert result.success is False
    assert result.conflicts == ["Verification timed out after 120 seconds."]
