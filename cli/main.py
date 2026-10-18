"""
cli/main.py
-----------
The terminal interface for Reqfix.
Provides three commands:
  - reqfix analyze   → show conflict report
  - reqfix fix       → generate fixed requirements.txt
  - reqfix install   → fix + auto-install packages
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.text import Text

from core.parser import RequirementsParser
from core.resolver import DependencyResolver
from core.fixer import Fixer
from core.installer import Installer
from core.verifier import Verifier, VerificationResult


# Single shared console instance for all output
console = Console()

# Default paths
DEFAULT_INPUT = "requirements.txt"
DEFAULT_OUTPUT = "requirements.fixed.txt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_banner() -> None:
    """Print the Reqfix welcome banner."""
    console.print(Panel.fit(
        "[bold cyan]Reqfix[/bold cyan] — Python Dependency Doctor\n"
        "[dim]Analyzes, fixes, and installs your requirements[/dim]",
        border_style="cyan"
    ))
    console.print()


def _run_analysis(filepath: str):
    """
    Shared logic used by all three commands:
    parse → resolve → fix.
    Returns (suggestions, resolved_packages, verification) tuple.
    """
    # Step 1: Parse
    try:
        parser = RequirementsParser(filepath)
        requirements = parser.parse()
    except FileNotFoundError as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        raise SystemExit(1)

    if not requirements:
        console.print("[yellow]⚠️  No packages found in requirements.txt[/yellow]")
        raise SystemExit(0)

    console.print(f"[dim]Found [bold]{len(requirements)}[/bold] packages in {filepath}[/dim]\n")

    # Step 2: Resolve against PyPI (with spinner)
    resolved_packages = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True  # clears the spinner after done
    ) as progress:
        task = progress.add_task("Checking PyPI for package versions...", total=None)
        resolver = DependencyResolver()
        resolved_packages = resolver.resolve(requirements)
        progress.update(task, description="Done checking PyPI ✓")

    # Step 3: Fix
    fixer = Fixer()
    suggestions = fixer.fix(resolved_packages)

    # Step 4: Verify all packages are mutually compatible
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Verifying cross-package compatibility...", total=None)
        verifier = Verifier()
        verification = verifier.verify(suggestions)
        progress.update(task, description="Verification complete ✓")

    if verification.success:
        console.print("[green]✅ All packages verified — no cross-package conflicts.[/green]\n")
    else:
        console.print("[bold yellow]⚠️  Cross-package conflicts detected:[/bold yellow]")
        for conflict in verification.conflicts:
            console.print(f"  [red]→ {conflict}[/red]")
        console.print(
            "\n[dim]Reqfix will still generate the best possible fix, "
            "but manual review may be needed.[/dim]\n"
        )

    return suggestions, resolved_packages, verification


def _print_report(
    suggestions,
    resolved_packages,
    verification: VerificationResult,
) -> None:
    """Print a detailed conflict + fix report table."""

    table = Table(
        title="📦 Dependency Report",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold cyan"
    )

    table.add_column("Package", style="bold white", min_width=15)
    table.add_column("Original", style="dim", min_width=12)
    table.add_column("Status", min_width=10)
    table.add_column("Suggested Fix", style="bold green", min_width=20)
    table.add_column("Reason", style="dim", min_width=30)

    conflicts = 0
    unpinned = 0
    healthy = 0

    for suggestion, resolved in zip(suggestions, resolved_packages):
        # Build status badge
        if resolved.error:
            status = Text("⚠ Error", style="bold yellow")
        elif suggestion.was_conflict:
            status = Text("💥 Conflict", style="bold red")
            conflicts += 1
        elif suggestion.was_unpinned:
            status = Text("📌 Unpinned", style="bold yellow")
            unpinned += 1
        else:
            status = Text("✅ Healthy", style="bold green")
            healthy += 1

        original = suggestion.original_specifier or "[dim]none[/dim]"

        table.add_row(
            suggestion.package_name,
            original,
            status,
            suggestion.fixed_line,
            suggestion.reason
        )

    console.print(table)
    console.print()

    # Summary line
    if verification.success:
        console.print(
            f"  [bold red]💥 Conflicts: {conflicts}[/bold red]   "
            f"[bold yellow]📌 Unpinned: {unpinned}[/bold yellow]   "
            f"[bold green]✅ Healthy: {healthy}[/bold green]"
        )
    else:
        console.print(
            f"  [bold red]💥 Conflicts: {conflicts}[/bold red]   "
            f"[bold yellow]📌 Unpinned: {unpinned}[/bold yellow]   "
            f"[bold yellow]⚠️ Cross-package conflicts: yes (see above)[/bold yellow]"
        )
    console.print()


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """
    Reqfix — Fix your Python dependency conflicts automatically.

    \b
    Commands:
      analyze   Show a conflict report without making changes
      fix       Generate a fixed requirements.txt
      install   Fix and auto-install all packages
    """
    pass


@cli.command()
@click.option(
    "--file", "-f",
    default=DEFAULT_INPUT,
    show_default=True,
    help="Path to your requirements.txt file"
)
def analyze(file: str) -> None:
    """
    Analyze requirements.txt and show a detailed conflict report.
    Does NOT make any changes to your files or environment.

    \b
    Example:
      reqfix analyze
      reqfix analyze --file path/to/requirements.txt
    """
    _print_banner()
    console.print("[bold]🔍 Analyzing dependencies...[/bold]\n")

    suggestions, resolved_packages, verification = _run_analysis(file)
    _print_report(suggestions, resolved_packages, verification)

    conflicts = sum(1 for s in suggestions if s.was_conflict)
    if conflicts > 0:
        console.print(
            f"[yellow]💡 Run [bold]reqfix fix[/bold] to generate a fixed requirements file.[/yellow]"
        )
    elif verification.success:
        console.print(
            "[green]🎉 No conflicts found! Run [bold]reqfix fix[/bold] to pin all versions safely.[/green]"
        )
    else:
        console.print(
            "[yellow]⚠️ Cross-package conflicts detected — review the messages above "
            "before installing.[/yellow]"
        )


@cli.command()
@click.option(
    "--file", "-f",
    default=DEFAULT_INPUT,
    show_default=True,
    help="Path to your requirements.txt file"
)
@click.option(
    "--output", "-o",
    default=DEFAULT_OUTPUT,
    show_default=True,
    help="Output path for the fixed requirements file"
)
def fix(file: str, output: str) -> None:
    """
    Generate a fixed requirements.txt with all versions pinned.
    Does NOT install anything — safe to run anytime.

    \b
    Example:
      reqfix fix
      reqfix fix --file requirements.txt --output requirements.fixed.txt
    """
    _print_banner()
    console.print("[bold]🔧 Generating fixed requirements...[/bold]\n")

    suggestions, resolved_packages, verification = _run_analysis(file)
    _print_report(suggestions, resolved_packages, verification)

    # Write fixed file
    fixer = Fixer()
    content = fixer.generate_fixed_requirements(suggestions)
    installer = Installer()

    try:
        path = installer.write_fixed_file(content, output)
        console.print(Panel.fit(
            f"[bold green]✅ Fixed requirements written to:[/bold green] [cyan]{path}[/cyan]\n\n"
            f"[dim]To install, run:[/dim]\n"
            f"[bold]  pip install -r {path}[/bold]\n"
            f"[dim]Or use:[/dim]\n"
            f"[bold]  reqfix install[/bold]",
            border_style="green"
        ))
    except (PermissionError, OSError) as e:
        console.print(f"[bold red]❌ Failed to write file:[/bold red] {e}")
        raise SystemExit(1)


@cli.command()
@click.option(
    "--file", "-f",
    default=DEFAULT_INPUT,
    show_default=True,
    help="Path to your requirements.txt file"
)
@click.option(
    "--output", "-o",
    default=DEFAULT_OUTPUT,
    show_default=True,
    help="Output path for the fixed requirements file"
)
@click.confirmation_option(
    prompt="⚠️  This will install/upgrade packages in your current environment. Continue?"
)
def install(file: str, output: str) -> None:
    """
    Fix requirements and auto-install all packages.
    Writes a fixed file AND runs pip install.

    \b
    Example:
      reqfix install
      reqfix install --file requirements.txt
    """
    _print_banner()
    console.print("[bold]🚀 Fixing and installing dependencies...[/bold]\n")

    suggestions, resolved_packages, verification = _run_analysis(file)
    _print_report(suggestions, resolved_packages, verification)

    if not verification.success:
        if not click.confirm(
            "Verification found conflicts. Install anyway?",
            default=False,
        ):
            raise SystemExit(0)

    # Write fixed file first
    fixer = Fixer()
    content = fixer.generate_fixed_requirements(suggestions)
    installer = Installer()

    try:
        path = installer.write_fixed_file(content, output)
        console.print(f"[dim]Fixed file written to {path}[/dim]\n")
    except (PermissionError, OSError) as e:
        console.print(f"[bold red]❌ Failed to write file:[/bold red] {e}")
        raise SystemExit(1)

    # Install packages with progress display
    console.print("[bold]📦 Installing packages...[/bold]\n")

    install_results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for suggestion in suggestions:
            task = progress.add_task(
                f"Installing [cyan]{suggestion.fixed_line}[/cyan]...",
                total=None
            )
            result = installer._install_package(suggestion.fixed_line)
            install_results.append(result)
            progress.remove_task(task)

            if result.success:
                console.print(f"  [green]✅ {suggestion.fixed_line}[/green]")
            else:
                console.print(f"  [red]❌ {suggestion.fixed_line}[/red] — {result.error}")

    # Final summary
    success_count = sum(1 for r in install_results if r.success)
    fail_count = len(install_results) - success_count

    console.print()
    console.print(Panel.fit(
        f"[bold green]✅ Installed: {success_count}[/bold green]   "
        f"[bold red]❌ Failed: {fail_count}[/bold red]",
        border_style="cyan",
        title="Installation Complete"
    ))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()