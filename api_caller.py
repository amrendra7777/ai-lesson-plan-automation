"""
api_caller.py — Two-provider API abstraction: Gemini (primary) -> Groq (fallback).

Provides a single call_api(prompt, temperature) function used by all LLM agents.

Retry logic:
- Always try Gemini first.
- On 503/429, immediately fall back to Groq for that call.
- If Groq also fails, alternate between the two with exponential backoff
  (1s -> 2s -> 4s ... capped at 30s) for up to 5 total attempts.
- After any successful call, next call always starts with Gemini again.
- All other exceptions are re-raised immediately.
"""

import time

from google import genai
from google.genai import types as genai_types
from google.genai import errors as genai_errors
from openai import OpenAI, APIStatusError

from rich.console import Console

import config

console = Console()

# -- Clients (lazy) -------------------------------------------------------------

_gemini_client = None
_groq_client = None


def _get_gemini() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        _gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _gemini_client


def _get_groq() -> OpenAI:
    global _groq_client
    if _groq_client is None:
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in .env")
        _groq_client = OpenAI(
            api_key=config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    return _groq_client


# -- Internal helpers -----------------------------------------------------------

def _is_overload(exc: Exception) -> bool:
    """Return True if the error is a 503/429 overload error."""
    error_str = str(exc)
    if isinstance(exc, genai_errors.APIError):
        code = getattr(exc, "code", None)
        return code in (429, 503) or "429" in error_str or "503" in error_str
    if isinstance(exc, APIStatusError):
        return exc.status_code in (429, 503)
    return "429" in error_str or "503" in error_str


def _call_gemini(prompt: str, temperature: float) -> str:
    response = _get_gemini().models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
        config=genai_types.GenerateContentConfig(temperature=temperature),
    )
    return response.text.strip()


def _call_groq(prompt: str, temperature: float) -> str:
    response = _get_groq().chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


# -- Public interface -----------------------------------------------------------

def call_api(prompt: str, temperature: float = 0.7) -> str:
    """
    Call the LLM API with Gemini-first, Groq-fallback logic.
    Retries up to 5 attempts total with exponential backoff on 503/429.
    Raises RuntimeError if all attempts are exhausted.
    """
    providers = [
        ("Gemini", lambda: _call_gemini(prompt, temperature)),
        ("Groq",   lambda: _call_groq(prompt, temperature)),
    ]

    delay = 1
    max_attempts = 5

    for attempt in range(1, max_attempts + 1):
        for name, caller in providers:
            console.print(f"[dim][API] Using {name} (attempt {attempt}/{max_attempts})...[/]")
            try:
                result = caller()
                return result
            except Exception as exc:
                if not _is_overload(exc):
                    raise
                next_name = providers[1][0] if name == "Gemini" else providers[0][0]
                console.print(
                    f"[bold yellow][API] {name} failed (503/429). "
                    f"Switching to {next_name}...[/]"
                )

        # Both providers failed this round -- wait before next attempt
        console.print(f"[dim][API] Both providers failed. Waiting {delay}s before retry...[/]")
        time.sleep(delay)
        delay = min(delay * 2, 30)

    raise RuntimeError(
        f"All API providers failed after {max_attempts} attempts. "
        "The APIs may be experiencing high demand. Try again later."
    )
