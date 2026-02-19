"""
core/fixer.py
-------------
Responsible for:
1. Suggesting the best pinned version for each package
2. Resolving conflicts by finding the nearest compatible version
3. Generating a clean fixed requirements.txt content
"""

from dataclasses import dataclass
from packaging.version import Version
from typing import Optional

from core.resolver import ResolvedPackage


@dataclass
class FixSuggestion:
    """
    Represents the fix suggestion for a single package.
    """
    package_name: str               # e.g. "flask"
    original_specifier: Optional[str]  # e.g. ">=2.0.0" or None
    suggested_version: Optional[str]   # e.g. "3.1.2"
    fixed_line: str                    # e.g. "flask==3.1.2"
    reason: str                        # human-readable explanation
    was_conflict: bool                 # was this package conflicting before?
    was_unpinned: bool                 # had no version constraint before?


class Fixer:
    """
    Analyzes resolved packages and produces fix suggestions.

    Strategy:
    - Conflicting packages  → suggest the closest available version
    - Unpinned packages     → pin to latest stable version
    - Already fine packages → pin to latest compatible version (safest)

    Usage:
        fixer = Fixer()
        suggestions = fixer.fix(resolved_packages)
        content = fixer.generate_fixed_requirements(suggestions)
    """

    def _pick_best_version(self, versions: list[str]) -> Optional[str]:
        """
        From a list of version strings, return the latest stable one.
        Returns None if the list is empty.
        """
        if not versions:
            return None

        # Sort and return the highest version
        return max(versions, key=lambda v: Version(v))

    def _find_closest_version(
        self,
        all_versions: list[str],
        specifier: Optional[str]
    ) -> Optional[str]:
        """
        When a specifier has NO compatible versions (conflict),
        find the closest available version to what was requested.

        Strategy: return the latest available stable version as a fallback.
        """
        if not all_versions:
            return None

        return max(all_versions, key=lambda v: Version(v))

    def fix_one(self, resolved: ResolvedPackage) -> FixSuggestion:
        """
        Generate a fix suggestion for a single resolved package.
        """
        name = resolved.requirement.name
        original_specifier = resolved.requirement.specifier
        was_conflict = resolved.is_conflict
        was_unpinned = original_specifier is None

        # --- Case 1: Error fetching from PyPI ---
        if resolved.error:
            return FixSuggestion(
                package_name=name,
                original_specifier=original_specifier,
                suggested_version=None,
                fixed_line=resolved.requirement.raw_line,  # keep original
                reason=f"Could not fetch from PyPI: {resolved.error}",
                was_conflict=False,
                was_unpinned=was_unpinned
            )

        # --- Case 2: Conflict — no version satisfies the constraint ---
        if was_conflict:
            closest = self._find_closest_version(
                resolved.available_versions,
                original_specifier
            )
            if closest:
                fixed_line = f"{name}=={closest}"
                reason = (
                    f"No version satisfies '{original_specifier}'. "
                    f"Pinned to latest available: {closest}"
                )
            else:
                fixed_line = resolved.requirement.raw_line
                reason = "Could not determine a fix — no versions available on PyPI."

            return FixSuggestion(
                package_name=name,
                original_specifier=original_specifier,
                suggested_version=closest,
                fixed_line=fixed_line,
                reason=reason,
                was_conflict=True,
                was_unpinned=was_unpinned
            )

        # --- Case 3: Unpinned — no version constraint at all ---
        if was_unpinned:
            best = self._pick_best_version(resolved.available_versions)
            fixed_line = f"{name}=={best}" if best else name
            reason = (
                f"No version was pinned. "
                f"Pinned to latest stable: {best}"
            )
            return FixSuggestion(
                package_name=name,
                original_specifier=None,
                suggested_version=best,
                fixed_line=fixed_line,
                reason=reason,
                was_conflict=False,
                was_unpinned=True
            )

        # --- Case 4: Has constraint, compatible versions exist (healthy) ---
        best_compatible = self._pick_best_version(resolved.compatible_versions)
        fixed_line = f"{name}=={best_compatible}" if best_compatible else name
        reason = (
            f"Pinned to latest compatible version: {best_compatible}"
        )

        return FixSuggestion(
            package_name=name,
            original_specifier=original_specifier,
            suggested_version=best_compatible,
            fixed_line=fixed_line,
            reason=reason,
            was_conflict=False,
            was_unpinned=False
        )

    def fix(self, resolved_packages: list[ResolvedPackage]) -> list[FixSuggestion]:
        """
        Generate fix suggestions for all resolved packages.
        Returns a list of FixSuggestion objects.
        """
        return [self.fix_one(resolved) for resolved in resolved_packages]

    def generate_fixed_requirements(self, suggestions: list[FixSuggestion]) -> str:
        """
        Generate the content of a clean fixed requirements.txt file.
        Returns a string ready to be written to a file.
        """
        header = (
            "# Generated by Reqfix\n"
            "# All packages pinned to latest compatible stable versions\n"
        )

        lines = [suggestion.fixed_line for suggestion in suggestions]
        return header + "\n".join(lines) + "\n"