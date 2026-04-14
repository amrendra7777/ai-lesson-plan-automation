"""
main.py — CLI entry point for the Lesson Plan Automation Pipeline.

Usage:
    python main.py --topic "Introduction to Python" --audience "Complete beginners"
"""

import argparse
import sys

from rich.console import Console

from pipeline import run_pipeline

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Lesson Plan Automation — Generate a complete 20-unit course.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python main.py --topic "Machine Learning Fundamentals" '
            '--audience "CS undergraduates"\n'
            '  python main.py --topic "Inglês para Negócios" '
            '--audience "Profissionais brasileiros"'
        ),
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Course topic, e.g. 'Introduction to Data Science'",
    )
    parser.add_argument(
        "--audience",
        required=True,
        help="Target audience, e.g. 'High school students with basic math skills'",
    )

    args = parser.parse_args()

    # Validate
    if not args.topic.strip():
        console.print("[bold red]Error:[/] --topic cannot be empty.")
        sys.exit(1)
    if not args.audience.strip():
        console.print("[bold red]Error:[/] --audience cannot be empty.")
        sys.exit(1)

    try:
        output_path = run_pipeline(
            topic=args.topic.strip(),
            audience=args.audience.strip(),
        )
        console.print(f"\n[bold]Done![/] Open your lesson plan at: [link]{output_path}[/link]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user.[/]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Pipeline failed:[/] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
