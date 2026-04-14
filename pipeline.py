"""
pipeline.py — Orchestrates the full 6-stage lesson plan generation pipeline.

Stages:
  1. Intake        → accept topic, audience, language
  2. Architect     → generate 20-unit syllabus (JSON)
  3. Iterator      → loop through each unit
  4. Drafter       → write lesson plan per unit (Markdown)
  5. QA Reviewer   → validate & finalize each lesson
  6. Aggregator    → combine all lessons into one Markdown file
"""

import json
import os
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text

from config import OUTPUT_DIR, LANGUAGE, TEST_MODE, UNIT_COUNT
from agents import generate_syllabus, draft_lesson, review_lesson

console = Console()


def _build_header(topic: str, audience: str, language: str) -> str:
    """Build a Markdown header block for the consolidated output file."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"# {topic}\n\n"
        f"**Target Audience:** {audience}  \n"
        f"**Language:** {language}  \n"
        f"**Generated on:** {now}  \n"
        f"**Total Units:** 20\n\n"
        "---\n\n"
    )


def _sanitize_filename(text: str) -> str:
    """Convert a topic string into a safe, clean filename."""
    safe = "".join(c if c.isalnum() or c in (" ", "-") else "" for c in text)
    return safe.strip().replace(" ", "_")[:80]


def run_pipeline(topic: str, audience: str, language: str | None = None) -> str:
    """
    Execute the full lesson plan generation pipeline.

    Args:
        topic:    Course topic string.
        audience: Target audience description.
        language: Output language (defaults to LANGUAGE from .env).

    Returns:
        Path to the generated consolidated Markdown file.
    """
    language = language or LANGUAGE

    # ── Stage 1: Intake ─────────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            f"[bold cyan]Course Topic:[/] {topic}\n"
            f"[bold cyan]Target Audience:[/] {audience}\n"
            f"[bold cyan]Language:[/] {language}",
            title="[bold]Pipeline Intake[/]",
            border_style="cyan",
        )
    )

    # -- Test Mode warning ----------------------------------------------------
    if TEST_MODE:
        console.print(
            "[bold red]WARNING: TEST MODE ENABLED -- generating "
            f"{UNIT_COUNT} units only[/]\n"
        )

    # -- Stage 2: Curriculum Architect ----------------------------------------
    console.print(f"\n[bold yellow]Stage 2:[/] Generating {UNIT_COUNT}-unit syllabus with Curriculum Architect...")
    syllabus = generate_syllabus(topic, audience, language)
    syllabus_json = json.dumps(syllabus, ensure_ascii=False, indent=2)
    console.print(f"[bold green]Syllabus generated[/] — {UNIT_COUNT} units received.\n")

    # Print syllabus overview
    for unit in syllabus:
        console.print(
            f"  [dim]Unit {unit['unit_number']:2d}:[/] {unit['unit_title']}"
        )
    console.print()

    # ── Stages 3-5: Iterate → Draft → QA ───────────────────────────────────
    finalized_lessons: list[str] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[bold]Processing units...[/]", total=UNIT_COUNT)

        for unit in syllabus:
            unit_num = unit["unit_number"]
            unit_title = unit["unit_title"]

            # Stage 4: Drafter
            progress.update(
                task,
                description=f"[cyan]Unit {unit_num}/{UNIT_COUNT}[/] — Drafting: {unit_title}",
            )
            draft = draft_lesson(unit, syllabus_json, language)

            # Stage 5: QA Reviewer
            progress.update(
                task,
                description=f"[yellow]Unit {unit_num}/{UNIT_COUNT}[/] — QA Review: {unit_title}",
            )
            final = review_lesson(draft)
            finalized_lessons.append(final)

            progress.advance(task)

    console.print(f"\n[bold green]All {UNIT_COUNT} units drafted and reviewed.[/]\n")

    # ── Stage 6: Output Aggregator ──────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{_sanitize_filename(topic)}_{timestamp}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    header = _build_header(topic, audience, language)
    consolidated = header + "\n\n".join(finalized_lessons)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(consolidated)

    console.print(
        Panel(
            f"[bold green]File saved to:[/] {filepath}\n"
            f"[dim]Total lessons:[/] {len(finalized_lessons)} / {UNIT_COUNT}",
            title="[bold]Pipeline Complete[/]",
            border_style="green",
        )
    )

    return filepath
