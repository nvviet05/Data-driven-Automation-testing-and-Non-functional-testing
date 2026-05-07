from non_functional.nfr_runner import run_non_functional_cases


def run() -> None:
    # TODO: Add real Moodle locators for assignment settings validation,
    # correction, save, and recovery confirmation.
    run_non_functional_cases(
        data_filename="f004_assignment_usability_data.csv",
        result_filename="f004_assignment_usability_results.csv",
        screenshot_prefix="F004_assignment_usability",
        planned_check="Verify assignment validation messages and corrected submission recovery.",
    )


if __name__ == "__main__":
    run()
