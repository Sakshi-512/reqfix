"""
core/resolver.py
----------------
Responsible for:
1. Fetching all available versions of a package from PyPI
2. Checking which versions satisfy the given constraints
3. Detecting conflicts (no version satisfies the constraint)
"""

import requests
from dataclasses import dataclass, field
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet, InvalidSpecifier
from typing import Optional

from core.parser import Requirement


# PyPI JSON API endpoint — free, no auth needed
PYPI_API_URL = "https://pypi.org/pypi/{package}/json"

# How long to wait for PyPI to respond (seconds)
REQUEST_TIMEOUT = 10


@dataclass
class ResolvedPackage:
    """
    Stores the resolution result for a single package.
    """
    requirement: Requirement          # original requirement
    available_versions: list[str]     # all versions on PyPI
    compatible_versions: list[str]    # versions that satisfy the constraint
    latest_version: Optional[str]     # latest stable version on PyPI
    is_conflict: bool = False         # True if no compatible version found
    error: Optional[str] = None       # any error message (network, not found etc)


class PyPIClient:
    """
    Handles all communication with the PyPI JSON API.

    Usage:
        client = PyPIClient()
        versions = client.fetch_versions("flask")
    """

    def __init__(self) -> None:
        # Reuse the same HTTP session for performance (connection pooling)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "reqfix/1.0.0"})

    def fetch_package_data(self, package_name: str) -> dict:
        """
        Fetch full package metadata from PyPI.
        Returns the raw JSON response as a dict.
        Raises exceptions on network errors or if package not found.
        """
        url = PYPI_API_URL.format(package=package_name)

        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        except requests.ConnectionError:
            raise ConnectionError(
                f"Could not connect to PyPI. Check your internet connection."
            )
        except requests.Timeout:
            raise TimeoutError(
                f"PyPI took too long to respond for package '{package_name}'."
            )

        if response.status_code == 404:
            raise LookupError(
                f"Package '{package_name}' not found on PyPI. Check the spelling."
            )

        response.raise_for_status()
        return response.json()

    def fetch_versions(self, package_name: str) -> tuple[list[str], str]:
        """
        Fetch all stable versions of a package from PyPI.
        Returns a tuple: (list of all versions, latest stable version)
        """
        data = self.fetch_package_data(package_name)

        # Filter out pre-releases (alpha, beta, rc) — keep only stable versions
        all_versions = []
        for version_str in data["releases"].keys():
            try:
                v = Version(version_str)
                if not v.is_prerelease and not v.is_devrelease:
                    all_versions.append(version_str)
            except InvalidVersion:
                # Skip malformed version strings
                continue

        # Sort versions from oldest to newest
        all_versions.sort(key=lambda v: Version(v))

        # Latest version is what PyPI considers the current stable release
        latest = data["info"]["version"]

        return all_versions, latest


class DependencyResolver:
    """
    Resolves all requirements against PyPI and identifies conflicts.

    Usage:
        resolver = DependencyResolver()
        results = resolver.resolve(requirements)
    """

    def __init__(self) -> None:
        self.client = PyPIClient()

    def _find_compatible_versions(
        self,
        versions: list[str],
        specifier_str: Optional[str]
    ) -> list[str]:
        """
        Filter versions down to only those that satisfy the specifier.
        If no specifier, all versions are compatible.
        """
        # No constraint means any version works
        if not specifier_str:
            return versions

        try:
            specifier = SpecifierSet(specifier_str)
        except InvalidSpecifier:
            # If specifier is malformed, we can't evaluate it
            return []

        return [v for v in versions if specifier.contains(v)]

    def resolve_one(self, requirement: Requirement) -> ResolvedPackage:
        """
        Resolve a single requirement against PyPI.
        Returns a ResolvedPackage with full resolution details.
        """
        try:
            all_versions, latest = self.client.fetch_versions(requirement.name)
        except (ConnectionError, TimeoutError, LookupError) as e:
            # Return a result with the error — don't crash the whole run
            return ResolvedPackage(
                requirement=requirement,
                available_versions=[],
                compatible_versions=[],
                latest_version=None,
                is_conflict=False,     # we don't know — it's an error, not a conflict
                error=str(e)
            )

        compatible = self._find_compatible_versions(all_versions, requirement.specifier)

        # It's a conflict if a specifier exists but nothing satisfies it
        is_conflict = bool(requirement.specifier) and len(compatible) == 0

        return ResolvedPackage(
            requirement=requirement,
            available_versions=all_versions,
            compatible_versions=compatible,
            latest_version=latest,
            is_conflict=is_conflict,
            error=None
        )

    def resolve(self, requirements: list[Requirement]) -> list[ResolvedPackage]:
        """
        Resolve all requirements.
        Returns a list of ResolvedPackage objects, one per requirement.
        """
        results = []
        for requirement in requirements:
            resolved = self.resolve_one(requirement)
            results.append(resolved)
        return results