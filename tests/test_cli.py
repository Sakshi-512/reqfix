"""Tests for cli.main analyze command."""

from click.testing import CliRunner

from cli.main import cli
from core.parser import Requirement
from core.resolver import ResolvedPackage
from core.verifier import VerificationResult


class _FakeDependencyResolver:
    def resolve(self, requirements: list[Requirement]) -> list[ResolvedPackage]:
        resolved = []
        for req in requirements:
            resolved.append(
                ResolvedPackage(
                    requirement=req,
                    available_versions=["2.0.0", "3.0.0"],
                    compatible_versions=["2.0.0", "3.0.0"],
                    latest_version="3.0.0",
                    is_conflict=False,
                    error=None,
                )
            )
        return resolved


class _FakeVerifier:
    def verify(self, suggestions):
        return VerificationResult(success=True, conflicts=[], raw_output="")


def test_analyze_command_with_mocked_resolver_and_verifier(tmp_path, monkeypatch):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text(
        "flask>=2.0.0\n"
        "requests==2.28.1\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("cli.main.DependencyResolver", _FakeDependencyResolver)
    monkeypatch.setattr("cli.main.Verifier", _FakeVerifier)

    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--file", str(req_file)])

    assert result.exit_code == 0
    assert "flask" in result.output
    assert "requests" in result.output
