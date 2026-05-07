from non_functional.nfr_runner import run_non_functional_cases


def run() -> None:
    # TODO: Add real Moodle locators for course state, enrolled user role, and
    # final status checks. Avoid deleting or modifying real course data.
    run_non_functional_cases(
        data_filename="f002_f005_data_integrity_data.csv",
        result_filename="f002_f005_data_integrity_results.csv",
        screenshot_prefix="F002_F005_data_integrity",
        planned_check="Compare final UI state with selected course, user, role, and status.",
    )


if __name__ == "__main__":
    run()
