"""Backward-compatible wrapper for performance NFR scripts.

Prefer running the final Project 3 modules directly:
- python -m non_functional.f003_quiz_performance_test
- python -m non_functional.f006_upload_performance_test
"""

from non_functional.f003_quiz_performance_test import run as run_quiz_performance
from non_functional.f006_upload_performance_test import run as run_upload_performance


def run() -> None:
    run_quiz_performance()
    run_upload_performance()


if __name__ == "__main__":
    run()
