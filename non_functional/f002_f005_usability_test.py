from non_functional.nfr_runner import run_non_functional_cases


def run() -> None:
    # TODO: Add real Moodle locators for create course and enroll users forms,
    # including validation messages and inputs that should remain filled.
    run_non_functional_cases(
        data_filename="f002_f005_usability_data.csv",
        result_filename="f002_f005_usability_results.csv",
        screenshot_prefix="F002_F005_usability",
        planned_check="Verify validation feedback and preservation of valid inputs.",
    )


if __name__ == "__main__":
    run()
