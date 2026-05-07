"""Backward-compatible wrapper for reliability NFR scripts.

Prefer running:
- python -m non_functional.f008_event_reliability_test
"""

from non_functional.f008_event_reliability_test import run as run_event_reliability


def run() -> None:
    run_event_reliability()


if __name__ == "__main__":
    run()
