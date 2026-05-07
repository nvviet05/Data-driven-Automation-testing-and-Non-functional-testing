from non_functional.nfr_runner import run_non_functional_cases


def run() -> None:
    # TODO: Add real Moodle locators for opening the course, adding a quiz,
    # filling quiz settings, saving, and confirming the created quiz.
    run_non_functional_cases(
        data_filename="f003_quiz_performance_data.csv",
        result_filename="f003_quiz_performance_results.csv",
        screenshot_prefix="F003_quiz_performance",
        planned_check="Measure quiz creation page load and submission response time.",
    )


if __name__ == "__main__":
    run()
