"""
core/parser.py
--------------
Responsible for reading and parsing a requirements.txt file.
Returns a clean list of package names and their version constraints.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Regex to match a valid requirement line like:
# flask>=2.0.0 or requests==2.28.1 or numpy
REQUIREMENT_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z0-9_.\-]+)"      # package name (dots allowed, e.g. zope.interface)
    r"(?P<specifier>[><=!~^,\s\d\.\*]*)?" # optional version specifier
    r"(?:\s*#.*)?$"                        # optional inline comment
)


@dataclass
class Requirement:
    """Represents a single parsed requirement from requirements.txt."""
    name: str                        # e.g. "flask"
    specifier: Optional[str]         # e.g. ">=2.0.0" or None
    raw_line: str                    # original line as-is for reference

    def __str__(self) -> str:
        if self.specifier:
            return f"{self.name}{self.specifier}"
        return self.name


class RequirementsParser:
    """
    Parses a requirements.txt file into a list of Requirement objects.

    Usage:
        parser = RequirementsParser("requirements.txt")
        requirements = parser.parse()
    """

    def __init__(self, filepath: str) -> None:
        self.filepath = Path(filepath)

    def _validate_file(self) -> None:
        """Check the file exists and is readable before parsing."""
        if not self.filepath.exists():
            raise FileNotFoundError(
                f"requirements.txt not found at: {self.filepath.resolve()}"
            )
        if not self.filepath.is_file():
            raise ValueError(
                f"Expected a file, but got a directory: {self.filepath}"
            )

    def _parse_line(self, line: str) -> Optional[Requirement]:
        """
        Parse a single line from requirements.txt.
        Returns a Requirement object or None if the line should be skipped.
        """
        stripped = line.strip()

        # Skip empty lines and comment lines
        if not stripped or stripped.startswith("#"):
            return None

        # Skip special pip flags like -r, -e, --index-url etc.
        if stripped.startswith("-"):
            return None

        match = REQUIREMENT_PATTERN.match(stripped)
        if not match:
            return None

        name = match.group("name").strip()
        specifier = match.group("specifier")

        # Clean up specifier — remove whitespace, set to None if empty
        if specifier:
            specifier = specifier.strip()
        specifier = specifier if specifier else None

        return Requirement(name=name, specifier=specifier, raw_line=line.rstrip())

    def parse(self) -> list[Requirement]:
        """
        Read and parse the requirements file.
        Returns a list of Requirement objects.
        """
        self._validate_file()

        requirements = []

        with self.filepath.open("r", encoding="utf-8") as f:
            for line in f:
                requirement = self._parse_line(line)
                if requirement:
                    requirements.append(requirement)

        return requirements