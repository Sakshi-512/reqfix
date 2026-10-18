"""Tests for core.resolver.DependencyResolver and PyPIClient."""

from core.parser import Requirement
from core.resolver import DependencyResolver, PyPIClient


FAKE_PYPI_RESPONSE = {
    "info": {"version": "2.0.0"},
    "releases": {
        "1.0.0": [],
        "1.5.0": [],
        "2.0.0": [],
        "3.0.0b1": [],
        "3.0.0rc1": [],
    },
}


def test_fetch_versions_filters_prereleases(monkeypatch):
    monkeypatch.setattr(
        PyPIClient,
        "fetch_package_data",
        lambda self, package_name: FAKE_PYPI_RESPONSE,
    )

    all_versions, latest = PyPIClient().fetch_versions("demo")

    assert all_versions == ["1.0.0", "1.5.0", "2.0.0"]
    assert latest == "2.0.0"
    assert "3.0.0b1" not in all_versions
    assert "3.0.0rc1" not in all_versions


def test_resolve_one_applies_specifier(monkeypatch):
    monkeypatch.setattr(
        PyPIClient,
        "fetch_package_data",
        lambda self, package_name: FAKE_PYPI_RESPONSE,
    )

    resolver = DependencyResolver()
    result = resolver.resolve_one(Requirement("demo", ">=1.5.0", "demo>=1.5.0"))

    assert result.compatible_versions == ["1.5.0", "2.0.0"]
    assert result.is_conflict is False
    assert result.error is None


def test_resolve_one_conflict_when_nothing_matches_specifier(monkeypatch):
    monkeypatch.setattr(
        PyPIClient,
        "fetch_package_data",
        lambda self, package_name: FAKE_PYPI_RESPONSE,
    )

    resolver = DependencyResolver()
    result = resolver.resolve_one(Requirement("demo", "==99.0", "demo==99.0"))

    assert result.compatible_versions == []
    assert result.is_conflict is True
    assert result.error is None


def test_resolve_one_connection_error_returns_error_field(monkeypatch):
    def raise_connection_error(self, package_name):
        raise ConnectionError("Could not connect to PyPI. Check your internet connection.")

    monkeypatch.setattr(PyPIClient, "fetch_package_data", raise_connection_error)

    resolver = DependencyResolver()
    result = resolver.resolve_one(Requirement("demo", None, "demo"))

    assert result.error is not None
    assert "Could not connect to PyPI" in result.error
    assert result.available_versions == []


def test_resolve_one_lookup_error_returns_error_field(monkeypatch):
    def raise_lookup_error(self, package_name):
        raise LookupError("Package 'demo' not found on PyPI. Check the spelling.")

    monkeypatch.setattr(PyPIClient, "fetch_package_data", raise_lookup_error)

    resolver = DependencyResolver()
    result = resolver.resolve_one(Requirement("demo", None, "demo"))

    assert result.error is not None
    assert "not found on PyPI" in result.error
