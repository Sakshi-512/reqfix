"""Tests for core.parser.RequirementsParser."""

import pytest

from core.parser import RequirementsParser, Requirement


def test_parse_valid_requirements(tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text(
        "flask>=2.0.0\n"
        "requests==2.28.1\n"
        "numpy\n",
        encoding="utf-8",
    )

    parsed = RequirementsParser(str(req_file)).parse()

    assert len(parsed) == 3
    assert parsed[0] == Requirement(
        name="flask", specifier=">=2.0.0", raw_line="flask>=2.0.0"
    )
    assert parsed[1] == Requirement(
        name="requests", specifier="==2.28.1", raw_line="requests==2.28.1"
    )
    assert parsed[2] == Requirement(name="numpy", specifier=None, raw_line="numpy")


def test_parse_dotted_package_name(tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("zope.interface==5.0\n", encoding="utf-8")

    parsed = RequirementsParser(str(req_file)).parse()

    assert len(parsed) == 1
    assert parsed[0].name == "zope.interface"
    assert parsed[0].specifier == "==5.0"


def test_parse_skips_comments_blank_lines_and_pip_flags(tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text(
        "\n"
        "# top-level comment\n"
        "  \n"
        "-r other.txt\n"
        "--index-url https://example.com\n"
        "flask>=2.0.0\n",
        encoding="utf-8",
    )

    parsed = RequirementsParser(str(req_file)).parse()

    assert len(parsed) == 1
    assert parsed[0].name == "flask"


def test_parse_inline_comment(tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.28.1  # pin for stability\n", encoding="utf-8")

    parsed = RequirementsParser(str(req_file)).parse()

    assert len(parsed) == 1
    assert parsed[0].name == "requests"
    assert parsed[0].specifier == "==2.28.1"
    assert parsed[0].raw_line == "requests==2.28.1  # pin for stability"


def test_missing_file_raises_file_not_found(tmp_path):
    missing = tmp_path / "does-not-exist.txt"
    parser = RequirementsParser(str(missing))

    with pytest.raises(FileNotFoundError, match="not found"):
        parser.parse()
