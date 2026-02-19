"""
core/installer.py
-----------------
Responsible for:
1. Writing the fixed requirements to a new file
2. Auto-installing the fixed packages using pip
3. Reporting installation success/failure per package
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from core.fixer import FixSuggestion


# Default output filename for the fixed requirements
FIXED_REQUIREMENTS_FILENAME = "requirements.fixed.txt"


@dataclass
class InstallResult:
    """
    Stores the result of installing a single package.
    """
    package: str          # e.g. "flask==3.1.2"
    success: bool         # True if pip install succeeded
    error: str | None     # pip error message if failed


class Installer:
    """
    Handles writing the fixed requirements file and installing packages.

    Usage:
        installer = Installer()
        installer.write_fixed_file(suggestions, "requirements.fixed.txt")
        results = installer.install(suggestions)
    """

    def write_fixed_file(
        self,
        content: str,
        output_path: str = FIXED_REQUIREMENTS_FILENAME
    ) -> Path:
        """
        Write the fixed requirements content to a file.
        Returns the Path of the written file.
        """
        path = Path(output_path)

        try:
            path.write_text(content, encoding="utf-8")
        except PermissionError:
            raise PermissionError(
                f"Cannot write to '{path}'. Check your file permissions."
            )
        except OSError as e:
            raise OSError(f"Failed to write fixed requirements file: {e}")

        return path

    def _install_package(self, package_line: str) -> InstallResult:
        """
        Install a single package using the current Python's pip.
        Uses subprocess to call pip safely — never uses os.system().
        """
        # sys.executable ensures we use the pip from the active virtualenv
        command = [sys.executable, "-m", "pip", "install", package_line, "--quiet"]

        try:
            result = subprocess.run(
                command,
                capture_output=True,   # capture stdout and stderr
                text=True,             # return strings not bytes
                timeout=120            # max 2 minutes per package
            )
        except subprocess.TimeoutExpired:
            return InstallResult(
                package=package_line,
                success=False,
                error=f"Installation timed out after 120 seconds."
            )
        except FileNotFoundError:
            return InstallResult(
                package=package_line,
                success=False,
                error="pip not found. Make sure Python and pip are installed correctly."
            )

        if result.returncode == 0:
            return InstallResult(package=package_line, success=True, error=None)
        else:
            # Extract the most useful part of pip's error output
            error_msg = result.stderr.strip() or result.stdout.strip()
            return InstallResult(
                package=package_line,
                success=False,
                error=error_msg
            )

    def install(self, suggestions: list[FixSuggestion]) -> list[InstallResult]:
        """
        Install all fixed packages one by one.
        Skips packages that had errors during resolution.
        Returns a list of InstallResult objects.
        """
        results = []

        for suggestion in suggestions:
            # Skip packages we couldn't fix (PyPI errors etc.)
            if suggestion.suggested_version is None:
                results.append(InstallResult(
                    package=suggestion.package_name,
                    success=False,
                    error="Skipped — no version could be determined."
                ))
                continue

            result = self._install_package(suggestion.fixed_line)
            results.append(result)

        return results

    def install_from_file(self, filepath: str) -> InstallResult:
        """
        Install all packages from a requirements file at once.
        Faster than installing one by one for large files.
        """
        command = [
            sys.executable, "-m", "pip", "install",
            "-r", filepath, "--quiet"
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=600   # 10 minutes for full file install
            )
        except subprocess.TimeoutExpired:
            return InstallResult(
                package=filepath,
                success=False,
                error="Installation timed out after 10 minutes."
            )

        if result.returncode == 0:
            return InstallResult(package=filepath, success=True, error=None)
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            return InstallResult(package=filepath, success=False, error=error_msg)