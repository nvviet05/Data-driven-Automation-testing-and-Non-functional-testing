from non_functional.nfr_runner import run_non_functional_cases


def run() -> None:
    # TODO: Add real Moodle locators for password fields, password policy
    # validation messages, and mismatched password confirmation checks.
    run_non_functional_cases(
        data_filename="f001_f007_security_data.csv",
        result_filename="f001_f007_security_results.csv",
        screenshot_prefix="F001_F007_security",
        planned_check="Verify password masking and weak or mismatched password rejection.",
    )


if __name__ == "__main__":
    run()
