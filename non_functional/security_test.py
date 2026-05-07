"""Backward-compatible wrapper for security NFR scripts.

Prefer running:
- python -m non_functional.f001_f007_security_test
"""

from non_functional.f001_f007_security_test import run as run_password_security


def run() -> None:
    run_password_security()


if __name__ == "__main__":
    run()
