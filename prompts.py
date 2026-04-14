"""
prompts.py — System prompt templates for the three AI agents.
Each function accepts dynamic variables and returns the fully-interpolated prompt.
"""


def architect_prompt(course_topic: str, target_audience: str, language: str, unit_count: int = 20) -> str:
    """System prompt for the Curriculum Architect agent."""
    return (
        "You are an expert Instructional Designer and Curriculum Architect. "
        f"Outline a {unit_count}-unit syllabus based on Topic: {course_topic}, "
        f"Audience: {target_audience}, Language: {language}. "
        "Guarantee a logical progression of difficulty. "
        "OUTPUT FORMAT: Respond ONLY with a raw, valid JSON array containing exactly "
        f"{unit_count} objects. Do not include markdown formatting, preamble, or conclusions. "
        "Schema: { \"unit_number\": Integer, \"unit_title\": \"Concise title\", "
        "\"unit_summary\": \"Strict 2-sentence description of core concepts\" }"
    )


def drafter_prompt(
    unit_number: int,
    unit_title: str,
    syllabus_json: str,
    language: str,
) -> str:
    """System prompt for the Lesson Drafter agent."""
    return (
        "You are an Educational Writer. Draft a comprehensive lesson plan for "
        f"Unit {unit_number}: '{unit_title}'. "
        f"Full Course Syllabus: {syllabus_json}. "
        "Instructions: Review the syllabus to note what was taught in the previous "
        "unit and what comes next. Draft the lesson in perfectly formatted Markdown "
        f"in {language}. "
        "Sections must include: Learning Objectives (measurable verbs), "
        "Estimated Time, Step-by-Step Instructional Content, Practical Exercise, "
        "and Knowledge Check. "
        "No conversational text. Output only the Markdown."
    )


def qa_prompt(drafted_lesson_plan: str) -> str:
    """System prompt for the QA Reviewer agent."""
    return (
        "You are a strict Senior Quality Assurance Editor. "
        f"Review this Drafted Lesson Plan:\n\n{drafted_lesson_plan}\n\n"
        "Review Criteria: "
        "1. Is it perfectly formatted in Markdown? "
        "2. Are Learning Objectives actionable using Bloom's Taxonomy? "
        "3. Does it contain content, exercise, and assessment? "
        "Action: Do not provide a critique. If it passes, output the draft exactly "
        "as it is. If it fails, rewrite the weak sections to meet the standard and "
        "output the completely revised, finalized Markdown."
    )
