"""
model_cycler.py — Handles exponential backoff and cycles through fallback models
on 503/429 API errors to ensure pipeline resilience under high demand.
"""

import time
from rich.console import Console
from google.genai import errors

import config

console = Console()

class ModelCycler:
    def __init__(self, starting_model: str):
        self.models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.5-pro",
            "gemini-pro-latest"
        ]
        
        # Move the starting_model to index 0
        if starting_model in self.models:
            self.models.remove(starting_model)
        self.models.insert(0, starting_model)
        
        self.current_index = 0
        self.fail_counts = {model: 0 for model in self.models}

    def get_current_model(self) -> str:
        return self.models[self.current_index]

    def _switch_model(self):
        old_model = self.get_current_model()
        self.current_index = (self.current_index + 1) % len(self.models)
        new_model = self.get_current_model()
        console.print(f"[bold yellow]Switching model from {old_model} to {new_model}[/]")

    def call_with_cycling(self, client, contents, **kwargs):
        full_rotations = 0
        start_index = self.current_index
        backoff_delay = 1
        
        while full_rotations < 3:
            current_model = self.get_current_model()
            
            try:
                response = client.models.generate_content(
                    model=current_model,
                    contents=contents,
                    **kwargs
                )
                # On success, reset the counter for this model
                self.fail_counts[current_model] = 0
                return response
                
            except errors.APIError as e:
                code = getattr(e, "code", None)
                
                # If code is missing, try string matching as fallback
                error_str = str(e)
                is_overload = (code in [429, 503]) or ("429" in error_str) or ("503" in error_str)
                
                if not is_overload:
                    # Re-raise any non-overload related exception
                    raise

                self.fail_counts[current_model] += 1
                console.print(
                    f"\n[bold red]Model {current_model} failed (Error 503/429). "
                    f"Fail count: {self.fail_counts[current_model]}[/]"
                )
                
                # Switch to the next model in the cycle
                self._switch_model()
                
                console.print(f"[dim]Waiting {backoff_delay}s before retry...[/]")
                time.sleep(backoff_delay)
                
                # Exponential backoff, capped at 30 seconds
                backoff_delay = min(backoff_delay * 2, 30)
                
                # Check rotation count
                if self.current_index == start_index:
                    full_rotations += 1
                    console.print(f"[bold magenta]Completed {full_rotations}/3 full model rotations.[/]")

        # If we exited the loop, all rotations failed
        raise RuntimeError(f"All {len(self.models)} models failed across 3 full rotations.")

# Instantiate a single shared instance
shared_cycler = ModelCycler(starting_model=config.GEMINI_MODEL)
