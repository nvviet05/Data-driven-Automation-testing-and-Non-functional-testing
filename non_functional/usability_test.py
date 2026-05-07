"""Backward-compatible wrapper for usability NFR scripts.

Prefer running the final Project 3 modules directly:
- python -m non_functional.f001_account_usability_test
- python -m non_functional.f002_f005_usability_test
- python -m non_functional.f004_assignment_usability_test
"""

from non_functional.f001_account_usability_test import run as run_account_usability
from non_functional.f002_f005_usability_test import run as run_course_enrol_usability
from non_functional.f004_assignment_usability_test import run as run_assignment_usability


def run() -> None:
    run_account_usability()
    run_course_enrol_usability()
    run_assignment_usability()


if __name__ == "__main__":
    run()
