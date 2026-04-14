"""
agents.py — LLM agent wrappers.
All API calls are routed through call_api() from api_caller.py,
which handles the Gemini-primary / Grok-fallback logic transparently.
"""

import json
import re

from api_caller import call_api
from config import ARCHITECT_TEMP, DRAFTER_TEMP, QA_TEMP, UNIT_COUNT
from prompts import architect_prompt, drafter_prompt, qa_prompt


def _extract_json_array(text: str) -> list:
    """
    Robustly extracts a JSON array from the LLM response.
    Handles cases where the model wraps JSON in markdown code fences.
    """
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    return json.loads(text)


# ── Agent 1: Curriculum Architect ───────────────────────────────────────────────
def generate_syllabus(topic: str, audience: str, language: str) -> list[dict]:
    """
    Calls the Curriculum Architect agent to produce a syllabus.
    Returns a list of UNIT_COUNT dicts with unit_number, unit_title, unit_summary.
    """
    prompt = architect_prompt(topic, audience, language, unit_count=UNIT_COUNT)
    raw = call_api(prompt, ARCHITECT_TEMP)
    syllabus = _extract_json_array(raw)

    if len(syllabus) != UNIT_COUNT:
        raise ValueError(
            f"Architect returned {len(syllabus)} units instead of {UNIT_COUNT}. "
            "Re-run or adjust the prompt."
        )
    return syllabus


# ── Agent 2: Lesson Drafter ─────────────────────────────────────────────────────
def draft_lesson(unit: dict, syllabus_json: str, language: str) -> str:
    """
    Calls the Lesson Drafter agent for a single unit.
    Returns a Markdown-formatted lesson plan.
    """
    prompt = drafter_prompt(
        unit_number=unit["unit_number"],
        unit_title=unit["unit_title"],
        syllabus_json=syllabus_json,
        language=language,
    )
    return call_api(prompt, DRAFTER_TEMP)


# ── Agent 3: QA Reviewer ───────────────────────────────────────────────────────
def review_lesson(drafted_md: str) -> str:
    """
    Calls the QA Reviewer agent to validate and polish a lesson draft.
    Returns the finalized Markdown.
    """
    prompt = qa_prompt(drafted_md)
    return call_api(prompt, QA_TEMP)
