from non_functional.nfr_runner import run_non_functional_cases


def run() -> None:
    # TODO: Add real Moodle locators for submission file picker/upload, save,
    # and confirmation. Use only small safe test files for timing.
    run_non_functional_cases(
        data_filename="f006_upload_performance_data.csv",
        result_filename="f006_upload_performance_results.csv",
        screenshot_prefix="F006_upload_performance",
        planned_check="Measure small file upload and submission response time.",
    )


if __name__ == "__main__":
    run()
