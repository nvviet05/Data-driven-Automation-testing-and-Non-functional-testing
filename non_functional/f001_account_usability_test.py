from non_functional.nfr_runner import run_non_functional_cases


def run() -> None:
    # TODO: Add real Moodle locators for required account fields and visible
    # validation feedback on the add user form.
    run_non_functional_cases(
        data_filename="f001_account_usability_data.csv",
        result_filename="f001_account_usability_results.csv",
        screenshot_prefix="F001_account_usability",
        planned_check="Check account form validation message visibility and text.",
    )


if __name__ == "__main__":
    run()
