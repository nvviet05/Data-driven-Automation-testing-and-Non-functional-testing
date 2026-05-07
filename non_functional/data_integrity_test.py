"""Backward-compatible wrapper for data integrity NFR scripts.

Prefer running:
- python -m non_functional.f002_f005_data_integrity_test
"""

from non_functional.f002_f005_data_integrity_test import run as run_course_enrol_integrity


def run() -> None:
    run_course_enrol_integrity()


if __name__ == "__main__":
    run()
