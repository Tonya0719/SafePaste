"""SafePaste local PII detection package."""

from dotenv import find_dotenv, load_dotenv


# Load project-local configuration before importing modules that read environment
# variables. Existing process environment variables keep precedence.
_dotenv_path = find_dotenv(usecwd=True)
if _dotenv_path:
    load_dotenv(_dotenv_path, override=False)

from .pipeline import SafePastePipeline

__all__ = ["SafePastePipeline"]
