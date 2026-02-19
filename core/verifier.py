"""
core/verifier.py
----------------
Responsible for verifying that ALL fixed packages are compatible
with each other — not just individually against PyPI.

This catches transitive dependency conflicts like:
  flask==3.1.2 needs werkzeug>=3.0.0
  but another package pins werkzeug==2.0.0
  → conflict! even though each package looked fine individually.

Strategy: use pip's own resolver via --dry-run to verify the
full set of pinned packages before anything is installed.
"""

import subprocess
import sys
import tempfile
import os
from dataclasses import dataclass

from core.fixer import FixSuggestion


@dataclass
class VerificationResult:
    """
    Result of verifying the full set of fixed packages together.
    """
    success: bool               # True if all packages are compatible
    conflicts: list[str]        # list of conflict messages from pip
    raw_output: str             # full pip output for debugging


class Verifier:
    """
    Verifies that all fixed packages are mutually compatible by
    running pip's resolver in dry-run mode (nothing gets installed).

    This is the difference between:
    - "flask 3.1.2 exists on PyPI" (what resolver.py checks)
    - "flask 3.1.2 + requests 2.28.1 + numpy 2.4.2 all work TOGETHER" (what this checks)

    Usage:
        verifier = Verifier()
        result = verifier.verify(suggestions)
    """

    def _build_requirements_lines(
        self,
        suggestions: list[FixSuggestion]
    ) -> list[str]:
        """
        Build a list of pinned requirement lines from fix suggestions.
        Skips packages that couldn't be resolved.
        """
        lines = []
        for suggestion in suggestions:
            # Only include packages we actually have a version for
            if suggestion.suggested_version:
                lines.append(suggestion.fixed_line)
        return lines

    def _parse_conflicts(self, pip_output: str) -> list[str]:
        """
        Extract conflict-related lines from pip's output.
        pip uses keywords like 'conflict', 'incompatible', 'ERROR'
        to signal resolution failures.
        """
        conflict_keywords = [
            "conflict",
            "incompatible",
            "ERROR",
            "cannot install",
            "ResolutionImpossible",
        ]

        conflicts = []
        for line in pip_output.splitlines():
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in conflict_keywords):
                cleaned = line.strip()
                if cleaned:
                    conflicts.append(cleaned)

        return conflicts

    def verify(self, suggestions: list[FixSuggestion]) -> VerificationResult:
        """
        Run pip's resolver in dry-run mode against all fixed packages.

        Steps:
        1. Write fixed packages to a temporary file
        2. Run: pip install -r tempfile --dry-run
        3. Parse output for conflicts
        4. Return result with details
        5. Clean up temp file automatically
        """
        lines = self._build_requirements_lines(suggestions)

        if not lines:
            return VerificationResult(
                success=False,
                conflicts=["No packages to verify."],
                raw_output=""
            )

        # Write to a temp file — automatically deleted when done
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8"
        ) as tmp:
            tmp.write("\n".join(lines))
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "pip", "install",
                    "-r", tmp_path,
                    "--dry-run",            # nothing gets installed
                    "--quiet",              # reduce noise
                    "--report", "-",        # output report to stdout
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            full_output = result.stdout + result.stderr
            conflicts = self._parse_conflicts(full_output)

            # pip returns exit code 1 if resolution fails
            success = result.returncode == 0

            # If pip succeeded but we found conflict keywords, still flag it
            if conflicts and success:
                success = False

            return VerificationResult(
                success=success,
                conflicts=conflicts,
                raw_output=full_output
            )

        except subprocess.TimeoutExpired:
            return VerificationResult(
                success=False,
                conflicts=["Verification timed out after 120 seconds."],
                raw_output=""
            )
        except Exception as e:
            return VerificationResult(
                success=False,
                conflicts=[f"Verification failed unexpectedly: {str(e)}"],
                raw_output=""
            )
        finally:
            # Always clean up the temp file, even if something crashes
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)